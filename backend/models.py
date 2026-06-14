# backend/models.py
from pydantic import BaseModel
from typing import Optional, List

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

class EnsembleParams(SignalParams):
    ensemble_n: int = 15

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

class ChatRequest(BaseModel):
    prompt: str
    message: str = ""
    signal_context: Optional[dict] = None
    current_node_id: str = ""
    graph_node_name: str = ""
    history: Optional[List[dict]] = None


class RadarParams(BaseModel):
    Pf: float = 1e-4
    R_ref: int = 4
    R_pro: int = 2
    drop_high_num: int = 10
    threshold_offset: float = 30.0
    qs: float = 0.01
    gate_dist: float = 16.0
    amp_drop_tol: float = 8.0

class LogRequest(BaseModel):
    message: str
    source: Optional[str] = None
    lineno: Optional[int] = None
    colno: Optional[int] = None
    error: Optional[str] = None

class ExplainRequest(BaseModel):
    name: str
    node_type: str
    chapter: Optional[str] = ""
    section: Optional[str] = ""
    topics: Optional[List[str]] = []

class TelemetryRequest(BaseModel):
    telemetry: dict
    signal: Optional[dict] = None
