# backend/radar_routes.py
import os
import threading
import numpy as np
import scipy.io
from fastapi import APIRouter, HTTPException
from backend.models import RadarParams
from backend.config import logger

router = APIRouter()

# Global cache for raw data
_raw_data_cache = None
_default_simulation_cache = None
_cache_lock = threading.Lock()

def get_raw_data():
    global _raw_data_cache
    with _cache_lock:
        if _raw_data_cache is None:
            mat_path = 'kalman_data/Raw_data.mat'
            if not os.path.exists(mat_path):
                logger.error("Raw_data.mat not found at: %s", mat_path)
                raise FileNotFoundError(f"数据文件不存在: {mat_path}")
            try:
                mat = scipy.io.loadmat(mat_path)
                raw_data = mat.get('raw_data')
                if raw_data is None:
                    raw_data = mat.get('Raw_data')
                if raw_data is None:
                    raise ValueError("MAT文件中未找到 raw_data 或 Raw_data 变量")
                _raw_data_cache = raw_data
                logger.info("Raw_data.mat 加载成功. 维度: %s", str(_raw_data_cache.shape))
            except Exception as e:
                logger.exception("加载MAT文件失败")
                raise e
        return _raw_data_cache

def generate_alpha_lut(Pf, max_N, drop_high_num):
    alpha_lut = np.zeros(max_N + 1)
    for n in range(1, max_N + 1):
        n_eff = n - drop_high_num
        if n_eff > 0:
            alpha_lut[n] = n_eff * (Pf**(-1.0 / n_eff) - 1.0)
        else:
            alpha_lut[n] = np.inf
    return alpha_lut

@router.on_event("startup")
def precompute_default_simulation():
    global _default_simulation_cache
    try:
        logger.info("正在后台预计算雷达默认参数仿真数据...")
        params = RadarParams()
        result = api_radar_track(params, use_cache=False)
        with _cache_lock:
            _default_simulation_cache = result
        logger.info("预计算雷达默认仿真数据成功，已置入全局缓存！")
    except Exception as e:
        logger.error(f"预计算雷达默认仿真数据失败: {e}")

def run_cmld_cfar_vectorized_opt(frame, margin, mask, alpha_lut, threshold_offset, drop_high_num):
    # Find candidate indices where frame value is greater than threshold_offset
    # Since thresholds = alpha_lut * noise_mean + threshold_offset, and noise_mean >= 0,
    # thresholds is always >= threshold_offset.
    # Thus, any pixel with frame value <= threshold_offset cannot possibly be a detection.
    # To optimize, we only compute CFAR for pixels exceeding threshold_offset.
    cand_x, cand_y = np.where(frame > threshold_offset)
    
    # Fallback to full vectorized method if candidate density is very high (dense noise or low offset)
    # 10000 is a safe threshold (approx 16% of 250x250 pixels)
    if len(cand_x) > 10000 or len(cand_x) == 0:
        if len(cand_x) == 0:
            return np.empty((0, 3))
        
        # Original fully-vectorized method
        padded_frame = np.pad(frame, pad_width=margin, mode='edge')
        windows = np.lib.stride_tricks.sliding_window_view(padded_frame, (2 * margin + 1, 2 * margin + 1))
        ref_cells = windows[:, :, mask]
        partitioned = np.partition(ref_cells, -drop_high_num, axis=-1)
        noise_mean = np.mean(partitioned[:, :, :-drop_high_num], axis=-1)
        N_actual = ref_cells.shape[-1]
        thresholds = alpha_lut[N_actual] * noise_mean + threshold_offset
        detections_mask = frame > thresholds
        x_indices, y_indices = np.where(detections_mask)
        Z = []
        for i, j in zip(x_indices, y_indices):
            Z.append((i + 1, j + 1, frame[i, j]))
        return np.array(Z) if Z else np.empty((0, 3))
    
    # Optimized candidate method (extremely fast for normal sparse/low-false-alarm signals)
    padded_frame = np.pad(frame, pad_width=margin, mode='edge')
    
    # Pre-calculate offset indices of the mask
    mask_indices = np.argwhere(mask) - margin # Shape: (N_mask, 2)
    
    N_cand = len(cand_x)
    cand_x_p = cand_x + margin
    cand_y_p = cand_y + margin
    
    # Vectorized indexing for candidate windows
    rows = cand_x_p[:, None] + mask_indices[None, :, 0]
    cols = cand_y_p[:, None] + mask_indices[None, :, 1]
    
    ref_cells = padded_frame[rows, cols] # Shape: (N_cand, N_mask)
    
    # Partition and calculate mean
    partitioned = np.partition(ref_cells, -drop_high_num, axis=-1)
    noise_mean = np.mean(partitioned[:, :-drop_high_num], axis=-1)
    
    N_actual = ref_cells.shape[-1]
    thresholds = alpha_lut[N_actual] * noise_mean + threshold_offset
    
    vals = frame[cand_x, cand_y]
    passed = vals > thresholds
    
    final_x = cand_x[passed]
    final_y = cand_y[passed]
    final_vals = vals[passed]
    
    Z = []
    for i, j, v in zip(final_x, final_y, final_vals):
        Z.append((i + 1, j + 1, v))
        
    return np.array(Z) if Z else np.empty((0, 3))

@router.post("/api/radar/track")
def api_radar_track(params: RadarParams, use_cache: bool = True):
    global _default_simulation_cache
    if use_cache:
        is_default = (
            abs(params.Pf - 1e-4) < 1e-9 and
            params.R_ref == 4 and
            params.R_pro == 2 and
            params.drop_high_num == 10 and
            abs(params.threshold_offset - 30.0) < 1e-9 and
            abs(params.qs - 0.01) < 1e-9 and
            abs(params.gate_dist - 16.0) < 1e-9 and
            abs(params.amp_drop_tol - 8.0) < 1e-9
        )
        if is_default and _default_simulation_cache is not None:
            logger.info("雷达仿真：命中默认参数全局缓存，直接返回结果")
            return _default_simulation_cache

    try:
        raw_data = get_raw_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载数据失败: {str(e)}")
        
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
    Q = params.qs * np.array([
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
    frames_history = []
    
    # Pre-calculate sliding window mask & LUT once outside the loop to save overhead
    margin = params.R_ref + params.R_pro
    max_N = (2 * margin + 1) ** 2
    alpha_lut = generate_alpha_lut(params.Pf, max_N, params.drop_high_num)
    
    mask = np.ones((2 * margin + 1, 2 * margin + 1), dtype=bool)
    mask[margin - params.R_pro : margin + params.R_pro + 1, margin - params.R_pro : margin + params.R_pro + 1] = False

    for k in range(num_frames):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        
        # 1. Target detection via vectorized & partitioned CMLD
        Z = run_cmld_cfar_vectorized_opt(frame_val, margin, mask, alpha_lut, params.threshold_offset, params.drop_high_num)
        
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
                        
                        if dist2 < params.gate_dist and (track_amp_dB - z_amp_dB) < params.amp_drop_tol:
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
                            
                            # Save first 5 steps math of tracking updates
                            if len(step_calculations) < 5:
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
                # No detections
                for t in tracks:
                    t['x'] = t['x_pred']
                    t['P'] = t['P_pred']
                    t['misses'] += 1
                    t['history'].append([t['x'][0], t['x'][2]])
                    if t['status'] == 'confirmed':
                        t['missed_pts'].append([t['x'][0], t['x'][2]])
        else:
            # No tracks
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
        
        # Capture current active tracks' valid points and misses for this frame snapshot
        current_active_paths = []
        current_active_misses = []
        for t in tracks:
            if t['status'] == 'confirmed':
                v_hist_len = len(t['history']) - t['misses']
                if v_hist_len > 0:
                    current_active_paths.append(t['history'][:v_hist_len])
                v_miss_len = len(t['missed_pts']) - t['misses']
                if v_miss_len > 0:
                    current_active_misses.extend(t['missed_pts'][:v_miss_len])
                    
        frames_history.append({
            "frame": k + 1,
            "false_alarms": list(accumulated_false_alarms),
            "misses": list(accumulated_valid_misses) + current_active_misses,
            "confirmed_paths": list(confirmed_paths) + current_active_paths,
            "stats": {
                "frame_idx": k + 1,
                "false_alarms_count": len(accumulated_false_alarms),
                "misses_count": len(accumulated_valid_misses) + len(current_active_misses),
                "track_points_count": sum(len(p) for p in confirmed_paths) + sum(len(p) for p in current_active_paths)
            }
        })
        if len(frames_history) > 200:
            frames_history = frames_history[-200:]
        
    # Process remaining alive tracks at the end
    for t in tracks:
        if t['status'] == 'confirmed':
            valid_hist_len = len(t['history']) - t['misses']
            if valid_hist_len > 0:
                confirmed_paths.append(t['history'][:valid_hist_len])
            valid_miss_len = len(t['missed_pts']) - t['misses']
            if valid_miss_len > 0:
                accumulated_valid_misses.extend(t['missed_pts'][:valid_miss_len])
                
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
        "step_calculations": step_calculations,
        "frames_history": frames_history
    }

@router.get("/api/radar/frame/{frame_idx}")
def api_radar_frame(frame_idx: int):
    if frame_idx < 1 or frame_idx > 50:
        raise HTTPException(status_code=400, detail="帧索引超出范围 (1..50)")
    try:
        raw_data = get_raw_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载数据失败: {str(e)}")
        
    # Get frame data (0-indexed in python)
    frame = np.abs(raw_data[:, :, frame_idx - 1])
    
    # Return JSON with indices and Z intensity
    return {
        "frame_idx": frame_idx,
        "z": frame.tolist()
    }
