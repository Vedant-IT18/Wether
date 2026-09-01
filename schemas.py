from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Location Schemas ---
class LocationSearchResult(BaseModel):
    id: Optional[int] = None
    name: str
    latitude: float
    longitude: float
    country: Optional[str] = "India"
    admin1: Optional[str] = None  # State / Province
    country_code: Optional[str] = "IN"
    display_name: str

class LocationSearchResponse(BaseModel):
    query: str
    results: List[LocationSearchResult]


# --- Current Weather Schemas ---
class CurrentWeather(BaseModel):
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    wind_direction: Optional[int] = 0
    rain_probability: int
    weather_code: int
    condition: str
    icon: str
    uv_index: float = 0.0
    sunrise: str = "06:00 AM"
    sunset: str = "06:45 PM"
    pressure: float = 1013.0
    is_day: int = 1
    time: str
    comfort_level: str

class CurrentWeatherResponse(BaseModel):
    location: LocationSearchResult
    current: CurrentWeather
    smart_advice: str
    is_demo: bool = False


# --- Hourly Forecast Schemas ---
class HourlyForecastItem(BaseModel):
    time: str
    hour_label: str
    temperature: float
    rain_probability: int
    weather_code: int
    condition: str
    icon: str
    wind_speed: float
    humidity: int

class HourlyForecastResponse(BaseModel):
    location: LocationSearchResult
    hourly: List[HourlyForecastItem]
    is_demo: bool = False


# --- 7-Day Forecast Schemas ---
class DailyForecastItem(BaseModel):
    date: str
    day_name: str
    full_date: str
    min_temp: float
    max_temp: float
    rain_probability: int
    weather_code: int
    condition: str
    icon: str
    sunrise: str
    sunset: str
    uv_index_max: float = 5.0

class DailyForecastResponse(BaseModel):
    location: LocationSearchResult
    daily: List[DailyForecastItem]
    is_demo: bool = False


# --- Alerts Schemas ---
class SmartAlert(BaseModel):
    id: str
    type: str  # e.g., "heavy_rain", "high_temp", "thunderstorm", "strong_wind"
    severity: str  # "info", "warning", "critical"
    title: str
    message: str
    expected_time: str
    location: str
    recommended_action: str
    icon: str = "⚠️"

class AlertsResponse(BaseModel):
    location: LocationSearchResult
    alerts: List[SmartAlert]
    total_active: int
    is_demo: bool = False


# --- Climate Insights Schemas ---
class ClimateTrendPoint(BaseModel):
    label: str
    historical_avg: float
    current_val: float
    anomaly: float

class ClimateInsightResponse(BaseModel):
    location: LocationSearchResult
    headline: str
    summary: str
    anomaly_c: float
    is_hotter: bool
    rainfall_anomaly_pct: float
    explanation: str
    trend_data: List[ClimateTrendPoint]
    is_demo: bool = False


# --- Chat Schemas ---
class ChatMessageRequest(BaseModel):
    message: str
    location: Optional[str] = "Nagpur"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    conversation_history: Optional[List[Dict[str, str]]] = []

class ChatMessageResponse(BaseModel):
    answer: str
    intent: str
    advice: Optional[str] = None
    alert: Optional[SmartAlert] = None
    weather_data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []
    timestamp: str
