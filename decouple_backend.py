import os

routes_path = 'backend/signal_routes.py'
engine_path = 'core/signal_engine.py'

with open(routes_path, 'r', encoding='utf-8') as f:
    routes_content = f.read()

functions_to_move = '''def _downsample(arr: np.ndarray, target=400):
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
'''

# Remove from signal_routes
routes_content = routes_content.replace(functions_to_move, '')

# Update import in signal_routes
routes_content = routes_content.replace(
    'from core.signal_engine import generate_signal, analyze_features, moving_average_filter, rc_lowpass_filter, _SIGNAL_GENERATORS',
    'from core.signal_engine import generate_signal, analyze_features, moving_average_filter, rc_lowpass_filter, _SIGNAL_GENERATORS, _downsample, _arr, generate_fine_clean'
)

with open(routes_path, 'w', encoding='utf-8') as f:
    f.write(routes_content)

# Append to signal_engine
with open(engine_path, 'a', encoding='utf-8') as f:
    f.write('\n\n# ── 路由辅助与高分重构 ───────────────────────────────────────────\n')
    f.write(functions_to_move)

print("Decoupled backend functions successfully.")
