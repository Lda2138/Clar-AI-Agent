"""随机信号分析 AI 助教 — FastAPI 启动入口"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8001, reload=True)
