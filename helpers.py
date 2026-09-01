from datetime import datetime
from typing import Dict, Any, Tuple

# WMO Weather interpretation codes (WW) mapping
WMO_CODE_MAP: Dict[int, Dict[str, str]] = {
    0: {"condition": "Clear Sky", "icon": "☀️", "category": "clear", "description": "Sunny and clear skies"},
    1: {"condition": "Mainly Clear", "icon": "🌤️", "category": "clear", "description": "Mostly sunny with slight clouds"},
    2: {"condition": "Partly Cloudy", "icon": "⛅", "category": "cloudy", "description": "Partly cloudy with scattered sunshine"},
    3: {"condition": "Overcast", "icon": "☁️", "category": "cloudy", "description": "Dense cloud cover"},
    45: {"condition": "Fog", "icon": "🌫️", "category": "fog", "description": "Foggy conditions with reduced visibility"},
    48: {"condition": "Depositing Rime Fog", "icon": "🌫️", "category": "fog", "description": "Dense freezing fog"},
    51: {"condition": "Light Drizzle", "icon": "🌦️", "category": "rain", "description": "Intermittent light drizzle"},
    53: {"condition": "Moderate Drizzle", "icon": "🌦️", "category": "rain", "description": "Steady light drizzle"},
    55: {"condition": "Dense Drizzle", "icon": "🌧️", "category": "rain", "description": "Heavy mist and dense drizzle"},
    56: {"condition": "Freezing Drizzle (Light)", "icon": "🌧️", "category": "rain", "description": "Freezing light drizzle"},
    57: {"condition": "Freezing Drizzle (Dense)", "icon": "🌧️", "category": "rain", "description": "Heavy freezing drizzle"},
    61: {"condition": "Slight Rain", "icon": "🌦️", "category": "rain", "description": "Passing light rain showers"},
    63: {"condition": "Moderate Rain", "icon": "🌧️", "category": "rain", "description": "Continuous moderate rainfall"},
    65: {"condition": "Heavy Rain", "icon": "🌧️", "category": "rain", "description": "Intense downpours and heavy rain"},
    66: {"condition": "Freezing Rain (Light)", "icon": "🌨️", "category": "rain", "description": "Light freezing rain"},
    67: {"condition": "Freezing Rain (Heavy)", "icon": "🌨️", "category": "rain", "description": "Severe freezing rain"},
    71: {"condition": "Slight Snow Fall", "icon": "🌨️", "category": "snow", "description": "Light flurries and snowfall"},
    73: {"condition": "Moderate Snow Fall", "icon": "❄️", "category": "snow", "description": "Moderate snowfall"},
    75: {"condition": "Heavy Snow Fall", "icon": "❄️", "category": "snow", "description": "Heavy blizzard-like snowfall"},
    77: {"condition": "Snow Grains", "icon": "❄️", "category": "snow", "description": "Scattered snow grains"},
    80: {"condition": "Slight Rain Showers", "icon": "🌦️", "category": "rain", "description": "Brief rain showers"},
    81: {"condition": "Moderate Rain Showers", "icon": "🌧️", "category": "rain", "description": "Scattered moderate rain showers"},
    82: {"condition": "Violent Rain Showers", "icon": "⛈️", "category": "storm", "description": "Sudden heavy rain bursts"},
    85: {"condition": "Slight Snow Showers", "icon": "🌨️", "category": "snow", "description": "Passing snow showers"},
    86: {"condition": "Heavy Snow Showers", "icon": "❄️", "category": "snow", "description": "Intense snow showers"},
    95: {"condition": "Thunderstorm", "icon": "⛈️", "category": "storm", "description": "Active thunderstorm with thunder and rain"},
    96: {"condition": "Thunderstorm with Slight Hail", "icon": "⛈️", "category": "storm", "description": "Thunderstorm accompanied by small hail"},
    99: {"condition": "Thunderstorm with Heavy Hail", "icon": "⛈️", "category": "storm", "description": "Severe thunderstorm with large hailstones"},
}

def get_wmo_details(code: int) -> Dict[str, str]:
    """Retrieve condition text, icon, and description for a WMO weather code."""
    return WMO_CODE_MAP.get(code, {
        "condition": "Clear Sky",
        "icon": "☀️",
        "category": "clear",
        "description": "Pleasant conditions"
    })

def format_iso_time(iso_str: str) -> str:
    """Converts ISO format '2026-09-01T14:00' to '2:00 PM'."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return iso_str

def format_iso_date(iso_str: str) -> Tuple[str, str]:
    """Converts ISO date to (Day Name e.g. 'Tue', Full Date e.g. 'Sep 1')."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%a"), dt.strftime("%b %d")
    except Exception:
        return "Today", iso_str

def calculate_comfort_level(temp_c: float, humidity: float, wind_kmh: float) -> str:
    """Provides a human comfort assessment."""
    if temp_c >= 40:
        return "Extreme Heat - Stay hydrated and indoors"
    elif temp_c >= 35:
        return "Hot and Sweltering"
    elif temp_c >= 28 and humidity > 70:
        return "Warm & Humid / Muggy"
    elif 20 <= temp_c <= 28 and humidity <= 65:
        return "Ideal & Very Pleasant"
    elif 15 <= temp_c < 20:
        return "Mild & Cool"
    elif 5 <= temp_c < 15:
        return "Chilly - Light jacket recommended"
    else:
        return "Cold - Heavy winter wear required"
