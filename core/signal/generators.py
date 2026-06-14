import numpy as np
from scipy import signal as scipy_signal
from typing import Dict, Tuple, Optional, Any

# ── 信号生成 ───────────────────────────────────────────


def generate_sine_wave(freq: float, fs: int, duration: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    return t, np.sin(2 * np.pi * freq * t)


def generate_square_wave(freq: float, fs: int, duration: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    return t, np.sign(np.sin(2 * np.pi * freq * t))


def generate_lfm_signal(freq_start: float, freq_end: float, fs: int, duration: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    k = (freq_end - freq_start) / duration
    phase = 2 * np.pi * (freq_start * t + 0.5 * k * t ** 2)
    return t, np.sin(phase)


def generate_gaussian_noise(n_samples: int, seed: Optional[int] = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0, 1, n_samples)


def add_noise_with_snr(signal_clean: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    """
    按指定信噪比 (dB) 将噪声叠加到信号上。
    SNR = 10 * log10(P_signal / P_noise)
    """
    p_signal = np.mean(signal_clean ** 2)
    p_noise = np.mean(noise ** 2)
    if p_noise == 0:
        return signal_clean.copy()
    desired_noise_power = p_signal / (10 ** (snr_db / 10))
    scale = np.sqrt(desired_noise_power / p_noise)
    return signal_clean + scale * noise


def generate_narrowband_signal(center_freq: float, fs: int, bandwidth: float = 50.0, duration: float = 1.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    生成平稳窄带随机信号。
    方法：白噪声通过理想带通滤波器，输出窄带高斯过程。
    """
    n_samples = int(fs * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    rng = np.random.default_rng(seed)

    # 用频域法：白噪声 → FFT → 带通滤波 → IFFT
    white_noise = rng.normal(0, 1, n_samples)
    fft_noise = np.fft.rfft(white_noise)
    freqs = np.fft.rfftfreq(n_samples, 1 / fs)

    # 理想带通滤波器
    mask = (np.abs(freqs - center_freq) <= bandwidth / 2)
    fft_noise[~mask] = 0
    narrowband = np.fft.irfft(fft_noise, n=n_samples)

    return t, narrowband


def generate_rayleigh_envelope(fs: int, center_freq: float = 200.0, bandwidth: float = 50.0, duration: float = 1.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    生成瑞利分布信号（窄带高斯噪声的包络）。
    R(t) = sqrt(I(t)² + Q(t)²)，其中 I(t), Q(t) 为低频正交分量。
    """
    n_samples = int(fs * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    rng = np.random.default_rng(seed)

    # 生成两路独立低通高斯噪声作为正交分量
    cutoff = bandwidth / 2
    nyquist = fs / 2
    b, a = scipy_signal.butter(4, cutoff / nyquist)

    i_comp = scipy_signal.lfilter(b, a, rng.normal(0, 1, n_samples))
    q_comp = scipy_signal.lfilter(b, a, rng.normal(0, 1, n_samples))

    envelope = np.sqrt(i_comp ** 2 + q_comp ** 2)
    return t, envelope



def generate_gaussian_white_noise(fs: int, duration: float = 1.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    n_samples = int(fs * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    rng = np.random.default_rng(seed)
    return t, rng.normal(0, 1, n_samples)


def generate_markov_process(a: float, fs: int, duration: float = 1.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    n_samples = int(fs * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    rng = np.random.default_rng(seed)
    # 输入白噪声的方差调整为 1 - a^2，使得平稳后方差为 1
    w = rng.normal(0, np.sqrt(max(1e-12, 1.0 - a ** 2)), n_samples)
    x = np.zeros(n_samples)
    x[0] = rng.normal(0, 1.0)
    for i in range(1, n_samples):
        x[i] = a * x[i - 1] + w[i]
    return t, x


def generate_triangle_wave(freq: float, fs: int, duration: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    return t, scipy_signal.sawtooth(2 * np.pi * freq * t, width=0.5)


def generate_dual_tone_sine(freq1: float, freq2: float, fs: int, duration: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    return t, 0.5 * (np.sin(2 * np.pi * freq1 * t) + np.sin(2 * np.pi * freq2 * t))


def _gen_sine(t, freq, n_samples, rng, snr_db, **kw):
    clean = np.sin(2 * np.pi * freq * t)
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

def _gen_square(t, freq, n_samples, rng, snr_db, **kw):
    clean = np.sign(np.sin(2 * np.pi * freq * t))
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

def _gen_narrowband(t, freq, fs, duration, seed, n_samples, rng, snr_db, **kw):
    inner_seed = (seed + 1) if seed is not None else None
    bandwidth = kw.get("bandwidth", 50.0)
    _, clean = generate_narrowband_signal(freq, fs, bandwidth=bandwidth, duration=duration, seed=inner_seed)
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

def _gen_rayleigh(t, freq, fs, duration, seed, n_samples, rng, snr_db, **kw):
    inner_seed = (seed + 1) if seed is not None else None
    bandwidth = kw.get("bandwidth", 50.0)
    _, clean = generate_rayleigh_envelope(fs, center_freq=freq, bandwidth=bandwidth, duration=duration, seed=inner_seed)
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

def _gen_lfm(t, freq, duration, n_samples, rng, snr_db, **kw):
    freq_end = kw.get("freq_end", freq + 100.0)
    k = (freq_end - freq) / duration
    phase = 2 * np.pi * (freq * t + 0.5 * k * t ** 2)
    clean = np.sin(phase)
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

def _gen_gaussian_white_noise(t, fs, duration, seed, n_samples, rng, snr_db, **kw):
    _, clean = generate_gaussian_white_noise(fs, duration, seed)
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

def _gen_markov(t, fs, duration, seed, n_samples, rng, snr_db, **kw):
    a = kw.get("markov_a", 0.9)
    _, clean = generate_markov_process(a, fs, duration, seed)
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

def _gen_triangle(t, freq, n_samples, rng, snr_db, **kw):
    clean = scipy_signal.sawtooth(2 * np.pi * freq * t, width=0.5)
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

def _gen_dual_tone(t, freq, n_samples, rng, snr_db, **kw):
    freq2 = kw.get("freq2", freq * 1.5)
    clean = 0.5 * (np.sin(2 * np.pi * freq * t) + np.sin(2 * np.pi * freq2 * t))
    noisy = add_noise_with_snr(clean, rng.normal(0, 1, n_samples), snr_db)
    return clean, noisy

_SIGNAL_GENERATORS = {
    "正弦+白噪声": _gen_sine,
    "方波+白噪声": _gen_square,
    "窄带":        _gen_narrowband,
    "瑞利分布":    _gen_rayleigh,
    "线性调频(LFM)": _gen_lfm,
    "高斯白噪声": _gen_gaussian_white_noise,
    "一阶马尔可夫过程": _gen_markov,
    "三角波+白噪声": _gen_triangle,
    "双频正弦+白噪声": _gen_dual_tone,
}


def generate_signal(signal_type: str, freq: float, fs: int, snr_db: float, duration: float = 1.0, seed: Optional[int] = None, **kwargs) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    统一信号生成接口，根据类型返回 (时轴, 纯净信号, 含噪信号)。
    """
    gen = _SIGNAL_GENERATORS.get(signal_type)
    if gen is None:
        raise ValueError(f"未知信号类型: {signal_type}")

    rng = np.random.default_rng(seed)
    n_samples = int(fs * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    clean, noisy = gen(t=t, freq=freq, fs=fs, duration=duration, seed=seed,
                       n_samples=n_samples, rng=rng, snr_db=snr_db, **kwargs)
    return t, clean, noisy


# ── 滤波算法 ───────────────────────────────────────────

def moving_average_filter(signal_data: np.ndarray, window_size: int = 10) -> np.ndarray:
    kernel = np.ones(window_size) / window_size
    return np.convolve(signal_data, kernel, mode="same")


def rc_lowpass_filter(signal_data: np.ndarray, fs: int, cutoff_freq: float = 500.0) -> np.ndarray:
    rc = 1.0 / (2 * np.pi * cutoff_freq)
    dt = 1.0 / fs
    alpha = dt / (rc + dt)
    filtered = np.zeros_like(signal_data)
    filtered[0] = signal_data[0]
    for i in range(1, len(signal_data)):
        filtered[i] = filtered[i - 1] + alpha * (signal_data[i] - filtered[i - 1])
    return filtered


def generate_high_res_clean(signal_type: str, freq: float, duration: float, **kwargs) -> np.ndarray:
    n_samples = 100000
    t = np.linspace(0, duration, n_samples, endpoint=False)
    # Add random phase offset to break phase locking (for periodic signals)
    if signal_type != "线性调频(LFM)":
        t += np.random.uniform(0, 1.0 / freq)
        
    if signal_type == "正弦+白噪声":
        return np.sin(2 * np.pi * freq * t)
    elif signal_type == "方波+白噪声":
        return np.sign(np.sin(2 * np.pi * freq * t))
    elif signal_type == "三角波+白噪声":
        return scipy_signal.sawtooth(2 * np.pi * freq * t, width=0.5)
    elif signal_type == "双频正弦+白噪声":
        freq2 = kwargs.get("freq2", freq * 1.5)
        return 0.5 * (np.sin(2 * np.pi * freq * t) + np.sin(2 * np.pi * freq2 * t))
    elif signal_type == "线性调频(LFM)":
        freq_end = kwargs.get("freq_end", freq + 100.0)
        k = (freq_end - freq) / duration
        phase = 2 * np.pi * (freq * t + 0.5 * k * t ** 2)
        return np.sin(phase)
    return np.zeros(n_samples)


def analyze_features(signal_data: np.ndarray, fs: int, clean_data: Optional[np.ndarray] = None,
                     signal_type: Optional[str] = None, freq: Optional[float] = None,
                     duration: Optional[float] = None, **kwargs) -> Dict[str, Any]:
    """
    计算信号的基本和高级特征。

    Args:
        signal_data: 信号数据数组 (含噪)
        fs: 采样率 (Hz)
        clean_data: 纯净信号数据数组 (可选)
        signal_type: 信号类型名称 (可选)
        freq: 中心/起始频率 (可选)
        duration: 信号持续时间 (可选)

    Returns:
        dict: 包含均值、方差、标准差、均方根、峰峰值、峭度、自相关、互相关、功率谱密度、相位谱、PDF直方图等
    """
    n = len(signal_data)
    mean_val = float(np.mean(signal_data))
    var_val = float(np.var(signal_data))
    std_val = float(np.std(signal_data))
    rms_val = float(np.sqrt(np.mean(signal_data ** 2)))
    pk_pk = float(np.ptp(signal_data))
    
    # 峭度 (Kurtosis) - 衡量分布的尖峭程度
    kurt = float(scipy_signal.kurtosis(signal_data)) if hasattr(scipy_signal, 'kurtosis') else 0.0

    # 自相关函数 (无偏估计)
    sig_centered = signal_data - mean_val
    autocorr = np.correlate(sig_centered, sig_centered, mode="full")
    autocorr = autocorr[n - 1:] / (n - np.arange(n))
    lags = np.arange(n) / fs

    # 功率谱密度 (Periodogram)
    freqs, psd = scipy_signal.periodogram(signal_data, fs)

    # 相位谱
    fft_noisy = np.fft.rfft(signal_data)
    phase = np.angle(fft_noisy)

    # PDF直方图
    pdf_y, bin_edges = np.histogram(signal_data, bins=50, density=True)
    pdf_x = (bin_edges[:-1] + bin_edges[1:]) / 2

    result = {
        "mean": mean_val,
        "variance": var_val,
        "std": std_val,
        "rms": rms_val,
        "peak_to_peak": pk_pk,
        "kurtosis": kurt,
        "autocorr": autocorr,
        "autocorr_lags": lags,
        "psd": psd,
        "psd_freqs": freqs,
        "phase": phase,
        "pdf_x": pdf_x,
        "pdf_y": pdf_y,
    }

    if clean_data is not None:
        if len(clean_data) == n:
            clean_mean = np.mean(clean_data)
            clean_centered = clean_data - clean_mean
            
            # 互相关函数 (无偏估计)
            crosscorr = np.correlate(clean_centered, sig_centered, mode="full")
            crosscorr = crosscorr[n - 1:] / (n - np.arange(n))
            
            # 纯净信号的功率谱、相位谱和PDF
            _, psd_clean = scipy_signal.periodogram(clean_data, fs)
            fft_clean = np.fft.rfft(clean_data)
            phase_clean = np.angle(fft_clean)
            
            # 针对确定性/周期信号使用高分辨率及随机相位生成平滑 PDF
            if signal_type in ["正弦+白噪声", "方波+白噪声", "三角波+白噪声", "双频正弦+白噪声", "线性调频(LFM)"] and freq is not None and duration is not None:
                clean_pdf_data = generate_high_res_clean(signal_type, freq, duration, **kwargs)
                pdf_y_clean, bin_edges_clean = np.histogram(clean_pdf_data, bins=50, density=True)
            else:
                pdf_y_clean, bin_edges_clean = np.histogram(clean_data, bins=50, density=True)
            pdf_x_clean = (bin_edges_clean[:-1] + bin_edges_clean[1:]) / 2
            
            result.update({
                "crosscorr": crosscorr,
                "crosscorr_lags": lags,
                "psd_clean": psd_clean,
                "phase_clean": phase_clean,
                "pdf_x_clean": pdf_x_clean,
                "pdf_y_clean": pdf_y_clean,
            })

    return result
