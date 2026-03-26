"""
Week 3 — FastAPI Application
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from api.routes import router

app = FastAPI(title="Fleet Intelligence Agent")
app.include_router(router)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


@app.get("/")
def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/vehicle")
def serve_vehicle():
    return FileResponse(FRONTEND_DIR / "vehicle.html")


@app.get("/branch")
def serve_branch():
    return FileResponse(FRONTEND_DIR / "branch.html")


@app.get("/chat")
def serve_chat():
    return FileResponse(FRONTEND_DIR / "chat.html")


@app.get("/health")
def health():
    return {"status": "ok"}
