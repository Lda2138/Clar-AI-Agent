import time
import numpy as np
import scipy.io
import os
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
    
    # We partition along axis=-1
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

def main():
    mat_path = 'kalman_data/Raw_data.mat'
    mat = scipy.io.loadmat(mat_path)
    raw_data = mat.get('raw_data')
    if raw_data is None:
        raw_data = mat.get('Raw_data')
    print("raw_data shape:", raw_data.shape)
    
    params = RadarParams()
    margin = params.R_ref + params.R_pro
    max_N = (2 * margin + 1) ** 2
    alpha_lut = generate_alpha_lut(params.Pf, max_N, params.drop_high_num)
    
    mask = np.ones((2 * margin + 1, 2 * margin + 1), dtype=bool)
    mask[margin - params.R_pro : margin + params.R_pro + 1, margin - params.R_pro : margin + params.R_pro + 1] = False
    
    t0 = time.time()
    for k in range(raw_data.shape[2]):
        frame_val = np.abs(raw_data[:, :, k]) ** 2
        Z = run_cmld_cfar_vectorized_opt(frame_val, margin, mask, alpha_lut, params.threshold_offset, params.drop_high_num)
    t1 = time.time()
    print("50 frames CMLD-CFAR took:", t1 - t0, "seconds")

if __name__ == "__main__":
    main()
