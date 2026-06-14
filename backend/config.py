# backend/config.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.agent_brain import SignalAgent

# Logger setup
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
    (["卡尔曼", "kalman", "状态空间", "状态方程", "观测方程", "一步预测", "卡尔曼增益", "递归估计", "状态估计"], "KP_CH2_03"),
    (["维纳滤波", "维纳预测", "wiener filter", "wiener", "mmse", "最小均方", "最佳线性"], "KP_CH2_02"),
    (["维纳-欣钦", "维纳欣钦", "wiener-khinchin", "功率谱密度", "psd", "谱分析", "傅里叶变换", "谱密度", "自相关函数与功率谱"], "KP_CH1_02"),
    (["白噪声", "线性系统", "lti", "冲激响应", "频率响应", "系统函数", "通过线性系统"], "KP_CH2_01"),
    (["平稳", "各态历经", "遍历性", "期望", "均值", "方差", "自相关", "互相关", "wss", "各态历经性", "宽平稳"], "KP_CH1_01"),
]

agent = None
try:
    agent = SignalAgent()
    logger.info("SignalAgent 初始化成功")
except ValueError as e:
    logger.warning("SignalAgent 未初始化: %s", e)
