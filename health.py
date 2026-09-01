from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "WeatherGPT API",
        "version": "1.0.0 (SIH 2026 Edition)",
        "timestamp": datetime.now().isoformat(),
        "nlp_engine": "Active (Heuristic + LLM Bridge)",
        "weather_provider": "Open-Meteo API"
    }
