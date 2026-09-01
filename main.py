import os
import sys
from pathlib import Path

# Add project root directory to sys.path so backend modules resolve properly when executed directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from backend.routes.weather import router as weather_router
from backend.routes.chat import router as chat_router
from backend.routes.climate import router as climate_router
from backend.routes.location import router as location_router
from backend.routes.health import router as health_router

app = FastAPI(
    title="WeatherGPT API",
    description="Conversational AI for Weather Forecasting, Alerts & Climate Information (Smart India Hackathon 2026)",
    version="1.0.0"
)

# CORS Middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(weather_router)
app.include_router(chat_router)
app.include_router(climate_router)
app.include_router(location_router)
app.include_router(health_router)

# Mount Frontend static files
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "WeatherGPT API is active. Frontend index.html not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
