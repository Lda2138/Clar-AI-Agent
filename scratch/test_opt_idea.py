import time
import numpy as np
import scipy.io
from backend.models import RadarParams

def generate_alpha_lut(Pf, max_N, drop_high_num):
    alpha_lut = np.zeros(max_N + 1)
    for n in range(1, max_N + 1):
        n_eff = n - drop_high_num
        if n_eff > 0:
            alpha_lut[n] = n_eff * (Pf**(-1.0 / n_eff) - 1.0)
        else:
            alpha_lut[n] = np.inf
    return alpha_lut

def run_cmld_cfar_vectorized_opt(frame, margin, mask, alpha_lut, threshold_offset, drop_high_num):
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

def run_cmld_cfar_candidate_opt(frame, margin, mask, alpha_lut, threshold_offset, drop_high_num):
    # Find candidate indices where frame value is greater than threshold_offset
    cand_x, cand_y = np.where(frame > threshold_offset)
    if len(cand_x) == 0:
        return np.empty((0, 3))
    
    padded_frame = np.pad(frame, pad_width=margin, mode='edge')
    
    # We want to extract the reference cells for each candidate pixel.
    # The coordinate of a pixel (x, y) in frame corresponds to (x + margin, y + margin) in padded_frame.
    # The reference window for (x, y) is padded_frame[x : x + 2*margin + 1, y : y + 2*margin + 1]
    
    # We can pre-calculate the offset indices of the mask
    mask_indices = np.argwhere(mask) - margin # Shape: (N_mask, 2)
    
    # For each candidate, get its reference cells
    # We can vectorize this:
    # cand_x_padded = cand_x + margin
    # cand_y_padded = cand_y + margin
    # coordinates of ref cells for candidate c: cand_x_padded[c] + mask_indices[:, 0], cand_y_padded[c] + mask_indices[:, 1]
    
    N_cand = len(cand_x)
    cand_x_p = cand_x + margin
    cand_y_p = cand_y + margin
    
    # Vectorized indexing:
    # We want shape: (N_cand, N_mask)
    # rows: cand_x_p[:, None] + mask_indices[None, :, 0]
    # cols: cand_y_p[:, None] + mask_indices[None, :, 1]
    rows = cand_x_p[:, None] + mask_indices[None, :, 0]
    cols = cand_y_p[:, None] + mask_indices[None, :, 1]
    
    ref_cells = padded_frame[rows, cols] # Shape: (N_cand, N_mask)
    
    # Partition and mean
    partitioned = np.partition(ref_cells, -drop_high_num, axis=-1)
    noise_mean = np.mean(partitioned[:, :-drop_high_num], axis=-1)
    
    N_actual = ref_cells.shape[-1]
    thresholds = alpha_lut[N_actual] * noise_mean + threshold_offset
    
    # Check which candidates exceed their thresholds
    vals = frame[cand_x, cand_y]
    passed = vals > thresholds
    
    final_x = cand_x[passed]
    final_y = cand_y[passed]
    final_vals = vals[passed]
    
    Z = []
    for i, j, v in zip(final_x, final_y, final_vals):
        Z.append((i + 1, j + 1, v))
        
    return np.array(Z) if Z else np.empty((0, 3))

def main():
    mat_path = 'kalman_data/Raw_data.mat'
    mat = scipy.io.loadmat(mat_path)
    raw_data = mat.get('raw_data')
    if raw_data is None:
        raw_data = mat.get('Raw_data')
        
    params = RadarParams()
    margin = params.R_ref + params.R_pro
    max_N = (2 * margin + 1) ** 2
    alpha_lut = generate_alpha_lut(params.Pf, max_N, params.drop_high_num)
    
    mask = np.ones((2 * margin + 1, 2 * margin + 1), dtype=bool)
    mask[margin - params.R_pro : margin + params.R_pro + 1, margin - params.R_pro : margin + params.R_pro + 1] = False
    
    # Let's count candidates per frame
    print("Default offset 30:")
    cands_counts = []
    for k in range(raw_data.shape[2]):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        cand_x, _ = np.where(frame_val > params.threshold_offset)
        cands_counts.append(len(cand_x))
    print(f"  Candidates per frame: min={min(cands_counts)}, max={max(cands_counts)}, mean={np.mean(cands_counts)}")
    
    # Test accuracy
    print("Verifying correctness...")
    correct = True
    for k in range(raw_data.shape[2]):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        Z_opt = run_cmld_cfar_vectorized_opt(frame_val, margin, mask, alpha_lut, params.threshold_offset, params.drop_high_num)
        Z_cand = run_cmld_cfar_candidate_opt(frame_val, margin, mask, alpha_lut, params.threshold_offset, params.drop_high_num)
        if not np.array_equal(Z_opt, Z_cand):
            print(f"Mismatch at frame {k}!")
            correct = False
            break
    if correct:
        print("SUCCESS: Candidate optimization matches vectorized results perfectly!")
        
    # Time it
    t0 = time.time()
    for k in range(raw_data.shape[2]):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        Z_cand = run_cmld_cfar_candidate_opt(frame_val, margin, mask, alpha_lut, params.threshold_offset, params.drop_high_num)
    t1 = time.time()
    print("50 frames Candidate CMLD-CFAR took:", t1 - t0, "seconds")

    # Time original
    t0 = time.time()
    for k in range(raw_data.shape[2]):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        Z_opt = run_cmld_cfar_vectorized_opt(frame_val, margin, mask, alpha_lut, params.threshold_offset, params.drop_high_num)
    t1 = time.time()
    print("50 frames Vectorized CMLD-CFAR took:", t1 - t0, "seconds")

    # Edge cases
    print("\nOffset 0 (dense):")
    offset_val = 0.0
    cands_counts = []
    for k in range(raw_data.shape[2]):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        cand_x, _ = np.where(frame_val > offset_val)
        cands_counts.append(len(cand_x))
    print(f"  Candidates per frame: min={min(cands_counts)}, max={max(cands_counts)}, mean={np.mean(cands_counts)}")

    # Time candidate with offset=0
    t0 = time.time()
    for k in range(raw_data.shape[2]):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        try:
            Z_cand = run_cmld_cfar_candidate_opt(frame_val, margin, mask, alpha_lut, offset_val, params.drop_high_num)
        except Exception as e:
            print("Candidate method errored:", e)
            break
    t1 = time.time()
    print("  Candidate method took:", t1 - t0, "seconds")

    # Time original with offset=0
    t0 = time.time()
    for k in range(raw_data.shape[2]):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        Z_opt = run_cmld_cfar_vectorized_opt(frame_val, margin, mask, alpha_lut, offset_val, params.drop_high_num)
    t1 = time.time()
    print("  Original method took:", t1 - t0, "seconds")

if __name__ == "__main__":
    main()
