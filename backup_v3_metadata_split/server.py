"""FastAPI backend for 随机信号分析 AI 助教"""
import sys
import os
import json
import logging
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Tuple
from scipy import signal as scipy_signal

from core.signal_engine import generate_signal, analyze_features, moving_average_filter, rc_lowpass_filter, _SIGNAL_GENERATORS
from core.agent_brain import SignalAgent, _clean_reply
from data.signal_knowledge_base import RANDOM_SIGNAL_KB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("server")

app = FastAPI(title="随机信号分析 AI 助教 Clar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

KP_KEYWORD_RULES = [
    (["维纳滤波", "最优滤波"], "KP_CH2_02"),
    (["卡尔曼", "kalman", "状态空间"], "KP_CH2_03"),
    (["平稳", "各态历经", "遍历性"], "KP_CH1_01"),
    (["维纳-欣钦", "维纳", "欣钦", "谱分析", "功率谱"], "KP_CH1_02"),
    (["白噪声"], "KP_CH2_01"),
]

agent = None
try:
    agent = SignalAgent()
    logger.info("SignalAgent 初始化成功")
except ValueError as e:
    logger.warning("SignalAgent 未初始化: %s", e)

# ═══════════════════════════════════════════════════════════
# API Models
# ═══════════════════════════════════════════════════════════

class SignalParams(BaseModel):
    signal_type: str = "正弦+白噪声"
    freq: float = 200.0
    fs: int = 10000
    snr_db: float = 10.0
    duration: float = 0.4
    bandwidth: Optional[float] = 50.0
    freq_end: Optional[float] = 300.0
    markov_a: Optional[float] = 0.9
    freq2: Optional[float] = 300.0

class FilterParams(BaseModel):
    signal_type: str = "正弦+白噪声"
    freq: float = 200.0
    fs: int = 10000
    snr_db: float = 10.0
    duration: float = 0.4
    filter_type: str = "moving_average"
    window_size: int = 10
    cutoff_freq: float = 500.0
    bandwidth: Optional[float] = 50.0
    freq_end: Optional[float] = 300.0
    markov_a: Optional[float] = 0.9
    freq2: Optional[float] = 300.0

class KalmanParams(BaseModel):
    q: float = 0.1
    r: float = 1.0
    v0: float = 1.0
    duration: float = 0.5
    fs: int = 1000

# 【修复 1：适配前端发送的新版嵌套 JSON 数据】
class ChatRequest(BaseModel):
    prompt: str
    message: str = ""
    signal_context: Optional[dict] = None
    current_node_id: str = ""
    graph_node_name: str = ""
    ui_mode: Optional[str] = "classic"
    history: Optional[list] = None

# ════════════# 【调试 2：接收前端控制台错误日志】
class LogRequest(BaseModel):
    message: str
    source: Optional[str] = None
    lineno: Optional[int] = None
    colno: Optional[int] = None
    error: Optional[str] = None

@app.post("/api/log")
def api_client_log(req: LogRequest):
    err_msg = f"[CLIENT ERROR] Msg: {req.message} | Src: {req.source} | Line: {req.lineno}:{req.colno} | Stack: {req.error}"
    logger.error(err_msg)
    try:
        with open("frontend_errors.log", "a", encoding="utf-8") as f:
            f.write(err_msg + "\n")
    except Exception as e:
        logger.error(f"Failed to write to frontend_errors.log: {e}")
    return {"status": "ok"}
# ════════════

# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _downsample(arr: np.ndarray, target=2000):
    if len(arr) <= target:
        return arr.tolist()
    step = max(1, len(arr) // target)
    return arr[::step].tolist()

def _arr(arr):
    if isinstance(arr, np.ndarray):
        return arr.tolist()
    return arr

# ═══════════════════════════════════════════════════════════
# API Routes
# ═══════════════════════════════════════════════════════════

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
        # 对于随机信号（窄带、瑞利、高斯白噪声、一阶马尔可夫），使用三次样条插值以保证与采样信号是同一实现且平滑
        if len(t_sampled) < 4:
            return t_sampled, clean_sampled
        try:
            from scipy.interpolate import interp1d
            f = interp1d(t_sampled, clean_sampled, kind='cubic', bounds_error=False, fill_value="extrapolate")
            clean_fine = f(t_fine)
        except Exception:
            return t_sampled, clean_sampled
            
    return t_fine, clean_fine


@app.post("/api/signal/generate")
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

        # 组织高级特征
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
            
            # 高级特征与时频域分离图表数据
            "autocorr": _downsample(feats["autocorr"]),
            "autocorr_lags": _downsample(feats["autocorr_lags"]),
            "crosscorr": _downsample(feats["crosscorr"]) if "crosscorr" in feats else [],
            "crosscorr_lags": _downsample(feats["crosscorr_lags"]) if "crosscorr_lags" in feats else [],
            "pdf_x": feats["pdf_x"].tolist(),
            "pdf_y": feats["pdf_y"].tolist(),
            "pdf_x_clean": feats["pdf_x_clean"].tolist() if "pdf_x_clean" in feats else [],
            "pdf_y_clean": feats["pdf_y_clean"].tolist() if "pdf_y_clean" in feats else [],
            "psd_clean": _downsample(feats["psd_clean"]) if "psd_clean" in feats else [],
            "psd_noisy": _downsample(feats["psd"]),
            "psd_freqs": _downsample(feats["psd_freqs"]),
            "phase_clean": _downsample(feats["phase_clean"]) if "phase_clean" in feats else [],
            "phase_noisy": _downsample(feats["phase"]),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("信号生成失败")
        raise HTTPException(status_code=500, detail=f"信号生成失败: {e}")


@app.post("/api/signal/filter")
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
            # 频域非因果维纳滤波 (Wiener Filter)
            X = np.fft.fft(noisy)
            S_fft = np.fft.fft(clean)
            N_fft = np.fft.fft(noisy - clean) # 实际噪声
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

        # 为滤波输出和输入含噪信号生成平滑的插值曲线
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
        logger.exception("滤波处理失败")
        raise HTTPException(status_code=500, detail=f"滤波处理失败: {e}")



@app.post("/api/signal/kalman")
def api_kalman_filter(params: KalmanParams):
    try:
        dt = 1.0 / params.fs
        n_samples = int(params.fs * params.duration)
        t = np.linspace(0, params.duration, n_samples, endpoint=False)
        
        # 状态向量: [位置, 速度]^T
        # 状态转移矩阵: F
        F = np.array([[1.0, dt],
                      [0.0, 1.0]])
        
        # 观测矩阵: H (仅能测量位置)
        H = np.array([[1.0, 0.0]])
        
        # 过程噪声协方差: Q (随机加速度驱动模型)
        Q = np.array([[ (dt**3)/3.0, (dt**2)/2.0 ],
                      [ (dt**2)/2.0, dt          ]]) * params.q
        
        # 测量噪声协方差: R (将输入的标准差 r 平方作为协方差)
        R = np.array([[params.r ** 2]])
        
        # 预分配数组
        x_true = np.zeros((n_samples, 2))
        x_true[0] = [0.0, params.v0]
        
        # 固定随机种子确保教学仿真的一致性
        rng = np.random.default_rng(42)
        
        w = rng.multivariate_normal([0.0, 0.0], Q, n_samples)
        v = rng.normal(0.0, params.r, n_samples)
        
        for k in range(1, n_samples):
            x_true[k] = F @ x_true[k-1] + w[k]
            
        z = x_true[:, 0] + v
        
        # 卡尔曼递归滤波
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
            # 1. Predict (预测)
            x_pred = F @ x_est[k-1]
            P_pred = F @ P @ F.T + Q
            
            # 2. Update (更新)
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
        logger.exception("卡尔曼滤波仿真失败")
        raise HTTPException(status_code=500, detail=f"卡尔曼滤波仿真失败: {e}")


class MetadataSplitStreamParser:
    """
    Robust stream parser that splits content at ===METADATA=== and
    only yields the text part in real time, buffering the metadata.
    """
    def __init__(self, separator="===METADATA==="):
        self.separator = separator
        self.buffer = ""
        self.sep_found = False
        self.metadata_buffer = ""

    def feed(self, chunk: str):
        if self.sep_found:
            self.metadata_buffer += chunk
            return ""
            
        self.buffer += chunk
        if self.separator in self.buffer:
            self.sep_found = True
            parts = self.buffer.split(self.separator, 1)
            text_part = parts[0]
            self.metadata_buffer = parts[1]
            return text_part
        else:
            sep_len = len(self.separator)
            buffer_len = len(self.buffer)
            
            # Find the longest prefix of separator that matches the suffix of buffer
            max_match_len = 0
            for i in range(1, min(sep_len, buffer_len) + 1):
                if self.separator.startswith(self.buffer[-i:]):
                    max_match_len = i
            
            if max_match_len > 0:
                text_to_yield = self.buffer[:-max_match_len]
                self.buffer = self.buffer[-max_match_len:]
                return text_to_yield
            else:
                text_to_yield = self.buffer
                self.buffer = ""
                return text_to_yield

    def get_remaining_text(self):
        if not self.sep_found:
            return self.buffer
        return ""

    def get_metadata(self):
        return self.metadata_buffer


def try_parse_json(text: str):
    # Try parsing text with list of repair suffixes and strict=False to handle control chars
    try:
        data = json.loads(text, strict=False)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    
    # Try suffix repairs for truncated JSON
    cleaned_text = re.sub(r'\\u[0-9a-fA-F]{0,3}$', '', text)
    cleaned_text = re.sub(r'\\$', '', cleaned_text)
    
    suffixes = [
        '" }',
        '"}',
        '"]}',
        '"] }',
        '"}}',
        '"} }',
        ' }',
        '}}'
    ]
    for suffix in suffixes:
        try:
            data = json.loads(cleaned_text + suffix, strict=False)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return None


def extract_metadata_robust(metadata_str: str, reply_text: str) -> dict:
    clean_str = metadata_str.strip()
    match_json = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_str, re.DOTALL)
    if match_json:
        clean_str = match_json.group(1).strip()
    else:
        if clean_str.startswith("```json"):
            clean_str = clean_str[7:]
        elif clean_str.startswith("```"):
            clean_str = clean_str[3:]
        if clean_str.endswith("```"):
            clean_str = clean_str[:-3]
        clean_str = clean_str.strip()

    data = try_parse_json(clean_str)
    if not data:
        data = {}

    node_id = data.get("node_id")
    if not node_id:
        node_match = re.search(r'"node_id"\s*:\s*"([^"]+)"', clean_str)
        if node_match:
            node_id = node_match.group(1)

    suggested_page = data.get("suggested_page", "none")
    sp_match = re.search(r'"suggested_page"\s*:\s*"([^"]+)"', clean_str)
    if sp_match:
        suggested_page = sp_match.group(1)

    if suggested_page.startswith("tool"):
        suggested_page = "toolbox"
    elif suggested_page.startswith("sign"):
        suggested_page = "signal-lab"
    elif suggested_page.startswith("know"):
        suggested_page = "knowledge-map"
    elif suggested_page not in ("toolbox", "signal-lab", "knowledge-map"):
        suggested_page = "none"

    generate_signal = data.get("generate_signal")
    if not generate_signal:
        gs_match = re.search(r'"generate_signal"\s*:\s*(\{.*?\})', clean_str, re.DOTALL)
        if gs_match:
            try:
                generate_signal = json.loads(gs_match.group(1), strict=False)
            except Exception:
                pass

    run_toolbox = data.get("run_toolbox")
    if not run_toolbox:
        rt_match = re.search(r'"run_toolbox"\s*:\s*(\{.*?\})', clean_str, re.DOTALL)
        if rt_match:
            try:
                run_toolbox = json.loads(rt_match.group(1), strict=False)
            except Exception:
                pass

    time_analysis_type = data.get("time_analysis_type")
    if not time_analysis_type:
        tat_match = re.search(r'"time_analysis_type"\s*:\s*"([^"]+)"', clean_str)
        if tat_match:
            time_analysis_type = tat_match.group(1)

    freq_analysis_type = data.get("freq_analysis_type")
    if not freq_analysis_type:
        fat_match = re.search(r'"freq_analysis_type"\s*:\s*"([^"]+)"', clean_str)
        if fat_match:
            freq_analysis_type = fat_match.group(1)

    new_card = data.get("new_card")
    if not new_card:
        nc_match = re.search(r'"new_card"\s*:\s*(\{.*?\})', clean_str, re.DOTALL)
        if nc_match:
            try:
                new_card = json.loads(nc_match.group(1), strict=False)
            except Exception:
                pass

    quick_questions = data.get("quick_questions", [])
    if not quick_questions:
        qq_match = re.search(r'"quick_questions"\s*:\s*(\[.*?\])', clean_str, re.DOTALL)
        if qq_match:
            try:
                quick_questions = json.loads(qq_match.group(1), strict=False)
            except Exception:
                pass

    return {
        "reply": reply_text.strip(),
        "node_id": node_id,
        "new_card": new_card,
        "quick_questions": quick_questions,
        "suggested_page": suggested_page,
        "generate_signal": generate_signal,
        "run_toolbox": run_toolbox,
        "time_analysis_type": time_analysis_type,
        "freq_analysis_type": freq_analysis_type
    }

@app.post("/api/chat")
def api_chat(req: ChatRequest):
    if agent is None:
        return {"code": 503, "reply": "请在 .env 文件中配置 DEEPSEEK_API_KEY 后重启服务。", "node_id": None, "suggested_page": "none"}

    signal_context = req.signal_context
    if signal_context and signal_context.get("signal_generated"):
        signal_context["generated"] = True  # 对齐 agent_brain 的预期

    knowledge_context = None
    if req.current_node_id and req.current_node_id != "__ai__":
        knowledge_context = {
            "current_node_id": req.current_node_id,
            "graph_node_name": req.graph_node_name,
        }

    user_prompt = req.prompt or req.message

    def event_generator():
        raw_accumulated = []
        ui_mode = req.ui_mode or "classic"
        stream = agent.chat_stream(user_prompt, signal_context, knowledge_context, require_json=True, ui_mode=ui_mode, history=req.history)
        
        parser = MetadataSplitStreamParser()
        for chunk in stream:
            raw_accumulated.append(chunk)
            text_part = parser.feed(chunk)
            if text_part:
                for char in text_part:
                    yield f"data: {json.dumps({'type': 'text', 'content': char}, ensure_ascii=False)}\n\n"
                    
        # Yield any remaining text
        remaining = parser.get_remaining_text()
        if remaining:
            for char in remaining:
                yield f"data: {json.dumps({'type': 'text', 'content': char}, ensure_ascii=False)}\n\n"
                
        full_raw = "".join(raw_accumulated)
        
        # Split the text reply and metadata block
        if "===METADATA===" in full_raw:
            parts = full_raw.split("===METADATA===", 1)
            reply_text = parts[0].strip()
            metadata_str = parts[1].strip()
        else:
            reply_text = full_raw.strip()
            metadata_str = ""

        # Clean only the reply text
        reply_str = _clean_reply(reply_text)
        
        node_id = None
        match_node = re.search(r"\[NODE:\s*(\w+)\]", reply_str)
        if match_node:
            node_id = match_node.group(1)
            reply_str = re.sub(r"\[NODE:\s*(\w+)\]", "", reply_str).strip()
            
        ai_data = extract_metadata_robust(metadata_str, reply_str)
        
        # 1. 尝试从 JSON 数据中提取 node_id
        if not node_id:
            node_id = ai_data.get("node_id")
            
        # 2. 如果依然没有解析出 node_id，执行基于关键词的后备规则（双重保障）
        if not node_id:
            combined_text = (user_prompt + " " + (ai_data.get("reply") or "")).lower()
            for keywords, kp_id in KP_KEYWORD_RULES:
                if any(kw in combined_text for kw in keywords):
                    node_id = kp_id
                    break

        new_card = ai_data.get("new_card")
        if not new_card and node_id:
            nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})
            node = nodes.get(node_id)
            if node:
                new_card = {
                    "title": node["title"],
                    "core_concept": node["core_concept"]
                }
        
        metadata = {
            "type": "metadata",
            "code": 200,
            "reply": ai_data["reply"],
            "new_card": new_card,
            "quick_questions": ai_data["quick_questions"],
            "suggested_page": ai_data["suggested_page"],
            "generate_signal": ai_data.get("generate_signal"),
            "run_toolbox": ai_data.get("run_toolbox"),
            "time_analysis_type": ai_data.get("time_analysis_type"),
            "freq_analysis_type": ai_data.get("freq_analysis_type"),
            "node_id": node_id
        }
        yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/knowledge/node/{node_id}")
def api_get_node(node_id: str):
    nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})
    node = nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"未找到节点 {node_id}")

    result = {
        "title": node["title"],
        "chapter": node["chapter"],
        "core_concept": node["core_concept"],
        "engineering_meaning": node["engineering_meaning"],
        "formulas": [],
        "errors": [],
    }
    for f_id in node.get("related_formulas", []):
        f = RANDOM_SIGNAL_KB.get("formulas", {}).get(f_id)
        if f:
            result["formulas"].append(f)
    for e_id in node.get("related_errors", []):
        e = RANDOM_SIGNAL_KB.get("error_warnings", {}).get(e_id)
        if e:
            result["errors"].append(e)
    return result


@app.get("/api/knowledge/graph")
def api_get_graph():
    syllabus = RANDOM_SIGNAL_KB.get("course_syllabus", {})
    nodes = []
    links = []

    def resolve_kp(topic_name, section_name):
        combined = topic_name + " " + section_name
        for keywords, kp_id in KP_KEYWORD_RULES:
            if any(kw in combined for kw in keywords):
                return kp_id
        return None

    chapter_idx = 0
    for chapter_name, sections in syllabus.items():
        chapter_short = chapter_name.split("_")[1] if "_" in chapter_name else chapter_name
        chapter_id = f"ch_{chapter_idx}"
        nodes.append({
            "id": chapter_id, "name": chapter_short,
            "symbolSize": 38, "category": 0,
            "itemStyle": {"color": "#4285f4"},
            "node_type": "chapter",
            "chapter": chapter_short,
        })
        for section_name, topics in sections.items():
            section_id = f"{chapter_id}_{section_name}"
            nodes.append({
                "id": section_id, "name": section_name,
                "symbolSize": 26, "category": 1,
                "itemStyle": {"color": "#34a853"},
                "node_type": "section",
                "chapter": chapter_short,
                "section": section_name,
                "topics": topics,
            })
            links.append({"source": chapter_id, "target": section_id})
            for topic in topics:
                topic_id = f"{section_id}_{topic}"
                color = "#ea4335" if any(kw in topic for kw in ["平稳", "维纳", "白噪声", "正态"]) else "#fbbc04"
                node_data = {
                    "id": topic_id, "name": topic,
                    "symbolSize": 18, "category": 2,
                    "itemStyle": {"color": color},
                    "node_type": "topic",
                    "chapter": chapter_short,
                    "section": section_name,
                }
                kp_id = resolve_kp(topic, section_name)
                if kp_id:
                    node_data["kp_node_id"] = kp_id
                nodes.append(node_data)
                links.append({"source": section_id, "target": topic_id})
        chapter_idx += 1

    return {"nodes": nodes, "links": links}


@app.get("/api/knowledge/quick-questions/{node_id}")
def api_quick_questions(node_id: str, count: int = 3):
    nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})
    node = nodes.get(node_id)

    fallback = [
        f"请详细解释「{node['title'] if node else '该知识点'}」的核心概念是什么？",
        "这个概念在工程实践中有哪些典型应用场景？",
        "能否用 Python 代码演示该概念的仿真验证过程？",
    ]

    if not node:
        return JSONResponse(
            {"code": 404, "questions": fallback},
            headers={"Cache-Control": "no-store"},
        )

    if agent is None:
        return JSONResponse(
            {"code": 503, "questions": fallback},
            headers={"Cache-Control": "no-store"},
        )

    try:
        questions = agent.get_smart_follow_ups(
            node_title=node["title"],
            core_concept=node["core_concept"],
            engineering_meaning=node.get("engineering_meaning", ""),
            count=count,
        )
        if questions and len(questions) >= 2:
            return JSONResponse(
                {"code": 200, "questions": questions},
                headers={"Cache-Control": "no-store"},
            )
    except Exception as e:
        logger.warning("智能追问生成失败: %s", e)

    return JSONResponse(
        {"code": 200, "questions": fallback},
        headers={"Cache-Control": "no-store"},
    )

class ExplainRequest(BaseModel):
    name: str
    node_type: str
    chapter: str = ""
    section: str = ""
    topics: list[str] = []
    ui_mode: Optional[str] = "classic"

@app.post("/api/knowledge/ai-explain")
def api_ai_explain(req: ExplainRequest):
    if agent is None:
        return {"reply": "AI 服务未配置，请在 .env 中设置 DEEPSEEK_API_KEY。", "title": req.name}

    kb_nodes = RANDOM_SIGNAL_KB.get("knowledge_nodes", {})

    kp_node = None
    for nid, ndata in kb_nodes.items():
        title_lower = ndata["title"].lower()
        name_lower = req.name.lower()
        if any(kw in name_lower for kw in title_lower.split()) or any(
            kw in title_lower for kw in name_lower.split()
        ):
            kp_node = ndata
            break

    if req.node_type == "chapter":
        prompt = (
            f"你是《随机信号分析》课程助教 Clar。学生正在学习章节「{req.name}」。\n"
            f"请生成一段教学引导（200-300 字）：\n"
            f"1. 本章的核心主题和研究对象\n"
            f"2. 本章在整体课程中的位置和重要性\n"
            f"3. 学习本章需要的前置知识\n"
            f"4. 学完本章能解决什么工程问题\n"
            f"风格：专业但不枯燥，有引导性。"
        )
    elif req.node_type == "section":
        topics_str = "、".join(req.topics) if req.topics else ""
        prompt = (
            f"你是《随机信号分析》课程助教 Clar。学生正在学习小节「{req.name}」"
            f"（所属章节：{req.chapter}）。\n"
            f"本节包含的知识点：{topics_str}\n"
            f"请生成一段讲解（200-300 字）：\n"
            f"1. 本节的核心概念及其物理/工程含义\n"
            f"2. 各知识点之间的逻辑关系\n"
            f"3. 一个具体的学习建议或避坑提醒\n"
            f"风格：清晰有条理，善用类比。"
        )
    else:
        prompt = (
            f"你是《随机信号分析》课程助教 Clar。学生在学习知识点「{req.name}」"
            f"（章节：{req.chapter}，小节：{req.section}）。\n"
        )
        if kp_node:
            prompt += (
                f"以下是该知识点的预设资料：\n"
                f"标题：{kp_node['title']}\n"
                f"核心概念：{kp_node['core_concept']}\n"
                f"工程意义：{kp_node['engineering_meaning']}\n\n"
                f"请结合以上资料，生成一段 200-300 字的精彩讲解，用具体例子说明。"
            )
        else:
            prompt += (
                f"请生成一段 200-300 字的讲解：\n"
                f"1. 这个概念的定义和直觉理解\n"
                f"2. 在随机信号分析中的作用或应用\n"
                f"3. 一个简单例子帮助理解\n"
                f"风格：通俗但不失严谨，用数学配合直觉。"
            )

    try:
        reply, _ = agent.chat(prompt, None, ui_mode=req.ui_mode)
        return {
            "reply": reply or f"关于「{req.name}」的 AI 讲解暂时无法生成，请稍后重试。",
            "title": req.name,
            "chapter": req.chapter,
            "section": req.section,
            "is_dynamic": True,
        }
    except Exception as e:
        logger.exception("AI 讲解生成失败")
        return {
            "reply": f"AI 讲解生成失败：{e}",
            "title": req.name,
            "chapter": req.chapter,
            "is_dynamic": True,
        }


frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")