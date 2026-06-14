# scratch/test_yw_kalman.py
import os
import time
import numpy as np
import scipy.io

def generate_alpha_lut(Pf, max_N, drop_high_num):
    alpha_lut = np.zeros(max_N + 1)
    for n in range(1, max_N + 1):
        n_eff = n - drop_high_num
        if n_eff > 0:
            alpha_lut[n] = n_eff * (Pf**(-1.0 / n_eff) - 1.0)
        else:
            alpha_lut[n] = np.inf
    return alpha_lut

def run_cmld_cfar_frame(frame, Pf, R_ref, R_pro, drop_high_num, threshold_offset):
    num_x, num_y = frame.shape
    margin = R_ref + R_pro
    max_N = (2 * margin + 1) ** 2
    alpha_lut = generate_alpha_lut(Pf, max_N, drop_high_num)
    
    # 1. Fast Vectorized CMLD for interior cells (margin <= i < num_x - margin)
    # Pad the frame to handle boundaries identically or close to MATLAB
    # But wait, let's implement the exact MATLAB logic for comparison.
    # To do it fast, we can use a loop but optimize the inner part.
    # Actually, let's see how fast a loop with slicing runs in Python.
    Z = []
    
    # Pre-calculate masks for different window sizes if needed, or do it dynamically.
    # Since 250x250 is small, a nested loop with slicing in Python takes about 0.2s per frame if optimized.
    # Let's write an optimized loop:
    for i in range(num_x):
        r_min = max(0, i - margin)
        r_max = min(num_x, i + margin + 1)
        gr_min = max(0, i - R_pro)
        gr_max = min(num_x, i + R_pro + 1)
        
        local_gr_min = gr_min - r_min
        local_gr_max = gr_max - r_min
        
        for j in range(num_y):
            c_min = max(0, j - margin)
            c_max = min(num_y, j + margin + 1)
            gc_min = max(0, j - R_pro)
            gc_max = min(num_y, j + R_pro + 1)
            
            # Slice large window
            window_large = frame[r_min:r_max, c_min:c_max]
            
            # Guard window slices
            local_gc_min = gc_min - c_min
            local_gc_max = gc_max - c_min
            
            # We want to extract ref cells (excluding the guard window)
            # Create a boolean mask of the window size
            mask = np.ones(window_large.shape, dtype=bool)
            mask[local_gr_min:local_gr_max, local_gc_min:local_gc_max] = False
            
            ref_cells = window_large[mask]
            N_actual = len(ref_cells)
            
            if N_actual > drop_high_num:
                # Fast sort & drop high
                sorted_cells = np.sort(ref_cells)
                noise_mean = np.mean(sorted_cells[:-drop_high_num])
                
                dynamic_threshold = alpha_lut[N_actual] * noise_mean + threshold_offset
                val = frame[i, j]
                if val > dynamic_threshold:
                    # i+1, j+1 for 1-based index matching MATLAB
                    Z.append((i + 1, j + 1, val))
                    
    return np.array(Z) if Z else np.empty((0, 3))

def run_cmld_cfar_vectorized(frame, Pf, R_ref, R_pro, drop_high_num, threshold_offset):
    num_x, num_y = frame.shape
    margin = R_ref + R_pro
    max_N = (2 * margin + 1) ** 2
    alpha_lut = generate_alpha_lut(Pf, max_N, drop_high_num)
    
    # Pad the frame with edge replication
    padded_frame = np.pad(frame, pad_width=margin, mode='edge')
    
    # Create sliding window view
    windows = np.lib.stride_tricks.sliding_window_view(padded_frame, (2 * margin + 1, 2 * margin + 1))
    
    # Create mask for reference cells (excluding guard cells)
    mask = np.ones((2 * margin + 1, 2 * margin + 1), dtype=bool)
    mask[margin - R_pro : margin + R_pro + 1, margin - R_pro : margin + R_pro + 1] = False
    
    # Extract reference cells for all pixels
    ref_cells = windows[:, :, mask]  # Shape: (num_x, num_y, N_actual)
    
    # Sort along the last axis
    sorted_cells = np.sort(ref_cells, axis=-1)
    
    # Discard largest drop_high_num cells and calculate mean
    noise_mean = np.mean(sorted_cells[:, :, :-drop_high_num], axis=-1)
    
    # Calculate threshold (since we pad, N_actual is always max_N - (2*R_pro+1)^2)
    N_actual = ref_cells.shape[-1]
    thresholds = alpha_lut[N_actual] * noise_mean + threshold_offset
    
    # Detect targets
    detections_mask = frame > thresholds
    x_indices, y_indices = np.where(detections_mask)
    
    Z = []
    for i, j in zip(x_indices, y_indices):
        Z.append((i + 1, j + 1, frame[i, j]))
        
    return np.array(Z) if Z else np.empty((0, 3))

def run_kalman_tracking(raw_data, Pf=1e-4, R_ref=4, R_pro=2, drop_high_num=10, threshold_offset=30, qs=0.01, gate_dist=16, amp_drop_tol=8):
    num_x, num_y, num_frames = raw_data.shape
    
    # Kalman matrices
    T = 1.0
    F = np.array([
        [1.0,  T,  0.0,  0.0],
        [0.0, 1.0,  0.0,  0.0],
        [0.0, 0.0,  1.0,  T  ],
        [0.0, 0.0,  0.0, 1.0]
    ])
    H = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0]
    ])
    Q = qs * np.array([
        [T**3/3.0, T**2/2.0,       0.0,       0.0],
        [T**2/2.0,        T,       0.0,       0.0],
        [     0.0,      0.0,  T**3/3.0,  T**2/2.0],
        [     0.0,      0.0,  T**2/2.0,        T]
    ])
    R = np.eye(2)
    
    tracks = []
    next_track_id = 1
    
    confirmed_paths = []
    accumulated_false_alarms = []
    accumulated_valid_misses = []
    
    # Store step-by-step calculation data for the first 5 steps of the first active track
    step_calculations = []
    
    for k in range(num_frames):
        frame = np.abs(raw_data[:, :, k]) ** 2
        
        # 1. Target detection via vectorized CMLD
        Z = run_cmld_cfar_vectorized(frame, Pf, R_ref, R_pro, drop_high_num, threshold_offset)
        
        # 2. Kalman prediction & data association
        assigned_Z_indices = []
        
        if len(tracks) > 0:
            # Predict step for all tracks
            for t in tracks:
                t['x_pred'] = F @ t['x']
                t['P_pred'] = F @ t['P'] @ F.T + Q
                
            if len(Z) > 0:
                cost_matrix = np.full((len(tracks), len(Z)), np.inf)
                for i, t in enumerate(tracks):
                    S_cov = H @ t['P_pred'] @ H.T + R
                    invS = np.linalg.inv(S_cov)
                    z_pred = H @ t['x_pred']
                    track_amp_dB = 10 * np.log10(t['amp'])
                    
                    for j in range(len(Z)):
                        z_meas = Z[j, 0:2]
                        dz = z_meas - z_pred
                        dist2 = dz.T @ invS @ dz
                        z_amp_dB = 10 * np.log10(Z[j, 2])
                        
                        if dist2 < gate_dist and (track_amp_dB - z_amp_dB) < amp_drop_tol:
                            cost_matrix[i, j] = dist2
                            
                # Associate measurements
                for i, t in enumerate(tracks):
                    min_dist = np.min(cost_matrix[i, :])
                    if not np.isinf(min_dist):
                        z_idx = np.argmin(cost_matrix[i, :])
                        if z_idx not in assigned_Z_indices:
                            assigned_Z_indices.append(z_idx)
                            z_meas = Z[z_idx, 0:2]
                            z_val = Z[z_idx, 2]
                            
                            # Kalman update
                            S_cov = H @ t['P_pred'] @ H.T + R
                            invS = np.linalg.inv(S_cov)
                            K = t['P_pred'] @ H.T @ invS
                            
                            x_old = t['x_pred'].copy()
                            P_old = t['P_pred'].copy()
                            
                            t['x'] = t['x_pred'] + K @ (z_meas - H @ t['x_pred'])
                            t['P'] = (np.eye(4) - K @ H) @ t['P_pred']
                            t['hits'] += 1
                            t['misses'] = 0
                            t['raw_meas'].append(z_meas.tolist())
                            t['amp'] = 0.8 * t['amp'] + 0.2 * z_val
                            
                            # Save first 5 steps math of confirmed tracks
                            if len(step_calculations) < 5 and t['status'] == 'confirmed':
                                step_calculations.append({
                                    "frame": k + 1,
                                    "track_id": t['id'],
                                    "x_pred": x_old.flatten().tolist(),
                                    "P_pred": P_old.tolist(),
                                    "z_meas": z_meas.tolist(),
                                    "K": K.tolist(),
                                    "x_est": t['x'].flatten().tolist(),
                                    "P_est": t['P'].tolist()
                                })
                            
                            if t['hits'] >= 3 and t['status'] == 'tentative':
                                t['status'] = 'confirmed'
                                
                            t['history'].append([t['x'][0], t['x'][2]])
                        else:
                            # Conflict / already assigned
                            t['x'] = t['x_pred']
                            t['P'] = t['P_pred']
                            t['misses'] += 1
                            t['history'].append([t['x'][0], t['x'][2]])
                            if t['status'] == 'confirmed':
                                t['missed_pts'].append([t['x'][0], t['x'][2]])
                    else:
                        # No measurement inside gate
                        t['x'] = t['x_pred']
                        t['P'] = t['P_pred']
                        t['misses'] += 1
                        t['history'].append([t['x'][0], t['x'][2]])
                        if t['status'] == 'confirmed':
                            t['missed_pts'].append([t['x'][0], t['x'][2]])
            else:
                # No detections at all
                for t in tracks:
                    t['x'] = t['x_pred']
                    t['P'] = t['P_pred']
                    t['misses'] += 1
                    t['history'].append([t['x'][0], t['x'][2]])
                    if t['status'] == 'confirmed':
                        t['missed_pts'].append([t['x'][0], t['x'][2]])
        
        # 3. Track initiation
        unassigned_Z_indices = [idx for idx in range(len(Z)) if idx not in assigned_Z_indices]
        for j in unassigned_Z_indices:
            z_meas = Z[j, 0:2]
            new_track = {
                'id': next_track_id,
                'x': np.array([z_meas[0], 0.0, z_meas[1], 0.0]),
                'P': np.diag([1.0, 10.0, 1.0, 10.0]),
                'status': 'tentative',
                'hits': 1,
                'misses': 0,
                'history': [[z_meas[0], z_meas[1]]],
                'raw_meas': [[z_meas[0], z_meas[1]]],
                'missed_pts': [],
                'amp': Z[j, 2]
            }
            next_track_id += 1
            tracks.append(new_track)
            
        # 4. Track deletion and tail trimming
        del_indices = []
        for i, t in enumerate(tracks):
            if t['status'] == 'confirmed' and t['misses'] >= 3:
                valid_hist_len = len(t['history']) - t['misses']
                if valid_hist_len > 0:
                    confirmed_paths.append(t['history'][:valid_hist_len])
                valid_miss_len = len(t['missed_pts']) - t['misses']
                if valid_miss_len > 0:
                    accumulated_valid_misses.extend(t['missed_pts'][:valid_miss_len])
                del_indices.append(i)
            elif t['status'] == 'tentative' and t['misses'] >= 2:
                accumulated_false_alarms.extend(t['raw_meas'])
                del_indices.append(i)
                
        # Remove deleted tracks
        tracks = [t for idx, t in enumerate(tracks) if idx not in del_indices]
        
    # Process remaining alive tracks at the end
    current_alive_misses = 0
    alive_track_points = 0
    for t in tracks:
        if t['status'] == 'confirmed':
            valid_hist_len = len(t['history']) - t['misses']
            if valid_hist_len > 0:
                confirmed_paths.append(t['history'][:valid_hist_len])
            valid_miss_len = len(t['missed_pts']) - t['misses']
            if valid_miss_len > 0:
                accumulated_valid_misses.extend(t['missed_pts'][:valid_miss_len])
                
    # Sum up points
    total_false_alarms = len(accumulated_false_alarms)
    total_misses = len(accumulated_valid_misses)
    total_track_points = sum(len(p) for p in confirmed_paths)
    
    return {
        "confirmed_paths": confirmed_paths,
        "false_alarms": accumulated_false_alarms,
        "misses": accumulated_valid_misses,
        "stats": {
            "num_frames": num_frames,
            "false_alarms_count": total_false_alarms,
            "misses_count": total_misses,
            "track_points_count": total_track_points
        },
        "step_calculations": step_calculations
    }

def test_tracking():
    mat_path = 'kalman_data/Raw_data.mat'
    if not os.path.exists(mat_path):
        print(f"Error: {mat_path} not found.")
        return
        
    print("Loading Raw_data.mat...")
    t0 = time.time()
    mat = scipy.io.loadmat(mat_path)
    # The variable inside is called 'raw_data' (lowercase in python scipy)
    raw_data = mat.get('raw_data')
    if raw_data is None:
        raw_data = mat.get('Raw_data')
    print(f"Loaded in {time.time() - t0:.2f}s. Shape: {raw_data.shape}")
    
    print("\n--- Running Kalman Tracking on 50 frames ---")
    t0 = time.time()
    results = run_kalman_tracking(raw_data)
    t_track = time.time() - t0
    print(f"Tracking simulation completed in {t_track:.3f}s.")
    print("Stats:")
    print(results["stats"])
    print(f"Number of confirmed paths: {len(results['confirmed_paths'])}")
    print(f"Step-by-step math steps saved: {len(results['step_calculations'])}")
    if len(results['step_calculations']) > 0:
        print("First math step summary:")
        step = results['step_calculations'][0]
        print(f"Frame: {step['frame']}, Track ID: {step['track_id']}")
        print(f"x_pred: {step['x_pred']}")
        print(f"z_meas: {step['z_meas']}")
        print(f"x_est: {step['x_est']}")

if __name__ == '__main__':
    test_tracking()
