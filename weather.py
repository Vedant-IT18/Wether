from fastapi import APIRouter, Query
from typing import Optional
from backend.models.schemas import (
    CurrentWeatherResponse,
    HourlyForecastResponse,
    DailyForecastResponse,
    AlertsResponse,
    LocationSearchResult
)
from backend.services.weather_service import weather_service, DEFAULT_LOCATION
from backend.services.alert_service import alert_service

router = APIRouter(prefix="/api/weather", tags=["weather"])

async def _build_location_obj(
    lat: float,
    lon: float,
    city: Optional[str] = None
) -> LocationSearchResult:
    if city:
        results = await weather_service.search_location(city)
        if results:
            return results[0]
    return LocationSearchResult(
        name=city or "Selected Location",
        latitude=lat,
        longitude=lon,
        country="India",
        admin1="",
        country_code="IN",
        display_name=city or f"Coordinates ({lat:.2f}, {lon:.2f})"
    )

@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
    lat: float = Query(21.1458, description="Latitude"),
    lon: float = Query(79.0882, description="Longitude"),
    location: Optional[str] = Query(None, description="City name")
):
    loc_obj = await _build_location_obj(lat, lon, location)
    return await weather_service.get_current_weather(lat, lon, loc_obj)

@router.get("/hourly", response_model=HourlyForecastResponse)
async def get_hourly_forecast(
    lat: float = Query(21.1458, description="Latitude"),
    lon: float = Query(79.0882, description="Longitude"),
    location: Optional[str] = Query(None, description="City name")
):
    loc_obj = await _build_location_obj(lat, lon, location)
    return await weather_service.get_hourly_forecast(lat, lon, loc_obj)

@router.get("/forecast", response_model=DailyForecastResponse)
async def get_daily_forecast(
    lat: float = Query(21.1458, description="Latitude"),
    lon: float = Query(79.0882, description="Longitude"),
    location: Optional[str] = Query(None, description="City name")
):
    loc_obj = await _build_location_obj(lat, lon, location)
    return await weather_service.get_daily_forecast(lat, lon, loc_obj)

@router.get("/alerts", response_model=AlertsResponse)
async def get_weather_alerts(
    lat: float = Query(21.1458, description="Latitude"),
    lon: float = Query(79.0882, description="Longitude"),
    location: Optional[str] = Query(None, description="City name")
):
    loc_obj = await _build_location_obj(lat, lon, location)
    return await alert_service.evaluate_alerts(lat, lon, loc_obj)
