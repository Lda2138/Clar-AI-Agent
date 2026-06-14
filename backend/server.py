"""FastAPI backend for 随机信号分析 AI 助教 - Clean and Modular version"""
import sys
import os
# Ensure the root directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.staticfiles import StaticFiles
from backend.config import app, logger
from backend.models import LogRequest
from backend.signal_routes import router as signal_router
from backend.chat_routes import router as chat_router
from backend.knowledge_routes import router as knowledge_router
from backend.radar_routes import router as radar_router

# Include modular routers
app.include_router(signal_router)
app.include_router(chat_router)
app.include_router(knowledge_router)
app.include_router(radar_router)

@app.post("/api/log")
def api_client_log(req: LogRequest):
    logger.error(f"[CLIENT ERROR] Msg: {req.message} | Src: {req.source} | Line: {req.lineno}:{req.colno} | Stack: {req.error}")
    return {"status": "ok"}

# Mount the static files for the frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")