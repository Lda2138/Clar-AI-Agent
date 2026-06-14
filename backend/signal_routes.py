# backend/signal_routes.py
import numpy as np
from typing import Tuple
from scipy import signal as scipy_signal
from fastapi import APIRouter, HTTPException

from backend.models import SignalParams, FilterParams, KalmanParams, EnsembleParams
from core.signal_engine import generate_signal, analyze_features, moving_average_filter, rc_lowpass_filter, _SIGNAL_GENERATORS

router = APIRouter()

def _downsample(arr: np.ndarray, target=400):
    if len(arr) <= target:
        return arr.tolist()
    step = max(1, len(arr) // target)
    return arr[::step].tolist()

def _arr(arr):
    if isinstance(arr, np.ndarray):
        return arr.tolist()
    return arr

def generate_fine_clean(signal_type: str, freq: float, fs: int, duration: float, t_sampled: np.ndarray, clean_sampled: np.ndarray, **kwargs) -> Tuple[np.ndarray, np.ndarray]:
    """
    为前端绘图生成高分辨率的纯净信号，解决低采样率下波形不平滑的问题。
    """
    target_points = 2000
    t_fine = np.linspace(0, duration, target_points, endpoint=False)
    
    if signal_type == "正弦+白噪声":
        clean_fine = np.sin(2 * np.pi * freq * t_fine)
    elif signal_type == "方波+白噪声":
        clean_fine = np.sign(np.sin(2 * np.pi * freq * t_fine))
    elif signal_type == "三角波+白噪声":
        clean_fine = scipy_signal.sawtooth(2 * np.pi * freq * t_fine, width=0.5)
    elif signal_type == "双频正弦+白噪声":
        freq2 = kwargs.get("freq2", freq * 1.5)
        clean_fine = 0.5 * (np.sin(2 * np.pi * freq * t_fine) + np.sin(2 * np.pi * freq2 * t_fine))
    elif signal_type == "线性调频(LFM)":
        freq_end = kwargs.get("freq_end", freq + 100.0)
        k = (freq_end - freq) / duration
        phase = 2 * np.pi * (freq * t_fine + 0.5 * k * t_fine ** 2)
        clean_fine = np.sin(phase)
    else:
        if len(t_sampled) < 4:
            return t_sampled, clean_sampled
        try:
            from scipy.interpolate import interp1d
            f = interp1d(t_sampled, clean_sampled, kind='cubic', bounds_error=False, fill_value="extrapolate")
            clean_fine = f(t_fine)
        except Exception:
            return t_sampled, clean_sampled
            
    return t_fine, clean_fine


@router.post("/api/signal/generate")
def api_generate_signal(params: SignalParams):
    if params.signal_type not in _SIGNAL_GENERATORS:
        raise HTTPException(status_code=400, detail=f"未知信号类型: {params.signal_type}")
    try:
        t, clean, noisy = generate_signal(
            params.signal_type, params.freq, params.fs, params.snr_db, params.duration,
            bandwidth=params.bandwidth, freq_end=params.freq_end,
            markov_a=params.markov_a, freq2=params.freq2
        )
        feats = analyze_features(
            noisy, params.fs, clean,
            signal_type=params.signal_type, freq=params.freq, duration=params.duration,
            freq2=params.freq2, freq_end=params.freq_end
        )

        n = len(clean)
        fs = params.fs
        freqs = np.fft.rfftfreq(n, 1 / fs)
        spec_clean = np.abs(np.fft.rfft(clean))
        spec_noisy = np.abs(np.fft.rfft(noisy))
        mask = freqs <= fs / 2

        t_fine, clean_fine = generate_fine_clean(
            params.signal_type, params.freq, params.fs, params.duration, t, clean,
            freq_end=params.freq_end, bandwidth=params.bandwidth, freq2=params.freq2
        )

        try:
            from scipy.interpolate import interp1d
            f_noisy = interp1d(t, noisy, kind='cubic', bounds_error=False, fill_value="extrapolate")
            noisy_fine = f_noisy(t_fine).tolist()
        except Exception:
            noisy_fine = _downsample(noisy)

        features_dict = {
            "mean": feats["mean"],
            "variance": feats["variance"],
            "std": feats["std"],
            "rms": feats["rms"],
            "peak_to_peak": feats["peak_to_peak"],
            "kurtosis": feats["kurtosis"],
        }

        return {
            "t": _downsample(t),
            "clean": _downsample(clean),
            "t_fine": t_fine.tolist(),
            "clean_fine": clean_fine.tolist(),
            "noisy": _downsample(noisy),
            "noisy_fine": noisy_fine,
            "freqs": _arr(freqs[mask]),
            "spec_clean": _arr(spec_clean[mask]),
            "spec_noisy": _arr(spec_noisy[mask]),
            "features": features_dict,
            
            "autocorr": _downsample(feats["autocorr"], target=3000),
            "autocorr_lags": _downsample(feats["autocorr_lags"], target=3000),
            "crosscorr": _downsample(feats["crosscorr"], target=3000) if "crosscorr" in feats else [],
            "crosscorr_lags": _downsample(feats["crosscorr_lags"], target=3000) if "crosscorr_lags" in feats else [],
            "pdf_x": feats["pdf_x"].tolist(),
            "pdf_y": feats["pdf_y"].tolist(),
            "pdf_x_clean": feats["pdf_x_clean"].tolist() if "pdf_x_clean" in feats else [],
            "pdf_y_clean": feats["pdf_y_clean"].tolist() if "pdf_y_clean" in feats else [],
            "psd_clean": _downsample(feats["psd_clean"]) if "psd_clean" in feats else [],
            "psd_noisy": _downsample(feats["psd"]),
            "psd_freqs": _downsample(feats["psd_freqs"]),
            "phase_clean": _arr(feats["phase_clean"]) if "phase_clean" in feats else [],
            "phase_noisy": _arr(feats["phase"]),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"信号生成失败: {e}")


@router.post("/api/signal/filter")
def api_filter_signal(params: FilterParams):
    if params.signal_type not in _SIGNAL_GENERATORS:
        raise HTTPException(status_code=400, detail=f"未知信号类型: {params.signal_type}")
    try:
        t, clean, noisy = generate_signal(
            params.signal_type, params.freq, params.fs, params.snr_db, params.duration,
            bandwidth=params.bandwidth, freq_end=params.freq_end,
            markov_a=params.markov_a, freq2=params.freq2
        )
        if params.filter_type == "moving_average":
            filtered = moving_average_filter(noisy, params.window_size)
        elif params.filter_type == "rc_lowpass":
            filtered = rc_lowpass_filter(noisy, params.fs, params.cutoff_freq)
        elif params.filter_type == "wiener":
            X = np.fft.fft(noisy)
            S_fft = np.fft.fft(clean)
            N_fft = np.fft.fft(noisy - clean)
            S_psd = np.abs(S_fft) ** 2
            N_psd = np.abs(N_fft) ** 2
            H_wiener = S_psd / (S_psd + N_psd + 1e-12)
            filtered = np.real(np.fft.ifft(X * H_wiener))
        else:
            raise HTTPException(status_code=400, detail=f"未知滤波类型: {params.filter_type}")

        feats = analyze_features(filtered, params.fs)

        n = len(noisy)
        fs = params.fs
        freqs = np.fft.rfftfreq(n, 1 / fs)
        spec_orig = np.abs(np.fft.rfft(noisy))
        spec_filt = np.abs(np.fft.rfft(filtered))
        mask = freqs <= fs / 2

        t_fine = np.linspace(0, params.duration, 2000, endpoint=False)
        try:
            from scipy.interpolate import interp1d
            f_filt = interp1d(t, filtered, kind='cubic', bounds_error=False, fill_value="extrapolate")
            filtered_fine = f_filt(t_fine).tolist()
            f_noisy = interp1d(t, noisy, kind='cubic', bounds_error=False, fill_value="extrapolate")
            noisy_fine = f_noisy(t_fine).tolist()
            t_fine_list = t_fine.tolist()
        except Exception:
            filtered_fine = _downsample(filtered)
            noisy_fine = _downsample(noisy)
            t_fine_list = _downsample(t)

        return {
            "filtered": _downsample(filtered),
            "filtered_fine": filtered_fine,
            "t_fine": t_fine_list,
            "noisy": _downsample(noisy),
            "noisy_fine": noisy_fine,
            "freqs": _arr(freqs[mask]),
            "spec_original": _arr(spec_orig[mask]),
            "spec_filtered": _arr(spec_filt[mask]),
            "features": {
                "mean": feats["mean"],
                "variance": feats["variance"],
                "std": feats["std"],
                "rms": feats["rms"],
                "peak_to_peak": feats["peak_to_peak"],
            },
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"滤波处理失败: {e}")


@router.post("/api/signal/kalman")
def api_kalman_filter(params: KalmanParams):
    try:
        dt = 1.0 / params.fs
        n_samples = int(params.fs * params.duration)
        t = np.linspace(0, params.duration, n_samples, endpoint=False)
        
        F = np.array([[1.0, dt],
                      [0.0, 1.0]])
        H = np.array([[1.0, 0.0]])
        Q = np.array([[ (dt**3)/3.0, (dt**2)/2.0 ],
                      [ (dt**2)/2.0, dt          ]]) * params.q
        R = np.array([[params.r ** 2]])
        
        x_true = np.zeros((n_samples, 2))
        x_true[0] = [0.0, params.v0]
        
        rng = np.random.default_rng(42)
        w = rng.multivariate_normal([0.0, 0.0], Q, n_samples)
        v = rng.normal(0.0, params.r, n_samples)
        
        for k in range(1, n_samples):
            x_true[k] = F @ x_true[k-1] + w[k]
            
        z = x_true[:, 0] + v
        
        x_est = np.zeros((n_samples, 2))
        x_est[0] = [0.0, params.v0]
        P = np.eye(2) * 1.0
        
        p_history = np.zeros(n_samples)
        k_gain_pos = np.zeros(n_samples)
        k_gain_vel = np.zeros(n_samples)
        
        p_history[0] = P[0, 0]
        k_gain_pos[0] = 0.0
        k_gain_vel[0] = 0.0
        
        for k in range(1, n_samples):
            # 1. Predict
            x_pred = F @ x_est[k-1]
            P_pred = F @ P @ F.T + Q
            
            # 2. Update
            S_val = (H @ P_pred @ H.T + R)[0, 0]
            K = (P_pred @ H.T / S_val).flatten()
            
            y_residual = z[k] - H @ x_pred
            x_est[k] = x_pred + K * y_residual
            P = (np.eye(2) - np.outer(K, H)) @ P_pred
            
            p_history[k] = P[0, 0]
            k_gain_pos[k] = K[0]
            k_gain_vel[k] = K[1]
            
        return {
            "t": t.tolist(),
            "pos_true": x_true[:, 0].tolist(),
            "pos_meas": z.tolist(),
            "pos_est": x_est[:, 0].tolist(),
            "vel_true": x_true[:, 1].tolist(),
            "vel_est": x_est[:, 1].tolist(),
            "p_error_pos": p_history.tolist(),
            "k_gain_pos": k_gain_pos.tolist(),
            "k_gain_vel": k_gain_vel.tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"卡尔曼滤波仿真失败: {e}")


@router.post("/api/signal/ensemble")
def api_ensemble_signal(params: EnsembleParams):
    if params.signal_type not in _SIGNAL_GENERATORS:
        raise HTTPException(status_code=400, detail=f"未知信号类型: {params.signal_type}")
    try:
        ensembles_noisy = []
        ensembles_clean = []
        all_noisy_concat = []
        
        # We need to compute an average PSD and a large combined PDF
        for i in range(params.ensemble_n):
            seed = (params.freq * params.fs) + i * 1000  # just a pseudo-random seed that changes with i
            t, clean, noisy = generate_signal(
                params.signal_type, params.freq, params.fs, params.snr_db, params.duration,
                bandwidth=params.bandwidth, freq_end=params.freq_end,
                markov_a=params.markov_a, freq2=params.freq2, seed=int(seed)
            )
            ensembles_noisy.append(_downsample(noisy))
            ensembles_clean.append(_downsample(clean))
            all_noisy_concat.extend(noisy)
            
        # Ultra-fast O(N) PDF calculation using np.histogram on the entire ensemble
        import numpy as np
        all_noisy = np.array(all_noisy_concat)
        counts, bins = np.histogram(all_noisy, bins=100, density=True)
        pdf_y = counts
        pdf_x = (bins[:-1] + bins[1:]) / 2

        return {
            "t": _downsample(t),
            "ensembles_noisy": ensembles_noisy,
            "ensembles_clean": ensembles_clean,
            "pdf_x_ensemble": pdf_x.tolist(),
            "pdf_y_ensemble": pdf_y.tolist(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系综信号生成失败: {e}")
