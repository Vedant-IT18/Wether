import httpx
import logging
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from backend.models.schemas import (
    LocationSearchResult,
    LocationSearchResponse,
    CurrentWeather,
    CurrentWeatherResponse,
    HourlyForecastItem,
    HourlyForecastResponse,
    DailyForecastItem,
    DailyForecastResponse
)
from backend.utils.helpers import (
    get_wmo_details,
    format_iso_time,
    format_iso_date,
    calculate_comfort_level
)

logger = logging.getLogger("weather_service")

# Fallback popular Indian cities
POPULAR_CITIES: List[Dict[str, Any]] = [
    {"name": "Nagpur", "latitude": 21.1458, "longitude": 79.0882, "country": "India", "admin1": "Maharashtra", "country_code": "IN"},
    {"name": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "country": "India", "admin1": "Maharashtra", "country_code": "IN"},
    {"name": "New Delhi", "latitude": 28.6139, "longitude": 77.2090, "country": "India", "admin1": "Delhi", "country_code": "IN"},
    {"name": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946, "country": "India", "admin1": "Karnataka", "country_code": "IN"},
    {"name": "Pune", "latitude": 18.5204, "longitude": 73.8567, "country": "India", "admin1": "Maharashtra", "country_code": "IN"},
    {"name": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867, "country": "India", "admin1": "Telangana", "country_code": "IN"},
    {"name": "Kolkata", "latitude": 22.5726, "longitude": 88.3639, "country": "India", "admin1": "West Bengal", "country_code": "IN"},
    {"name": "Chennai", "latitude": 13.0827, "longitude": 80.2707, "country": "India", "admin1": "Tamil Nadu", "country_code": "IN"},
    {"name": "Shimla", "latitude": 31.1048, "longitude": 77.1734, "country": "India", "admin1": "Himachal Pradesh", "country_code": "IN"},
    {"name": "Jaipur", "latitude": 26.9124, "longitude": 75.7873, "country": "India", "admin1": "Rajasthan", "country_code": "IN"},
]

DEFAULT_LOCATION = LocationSearchResult(
    id=1,
    name="Nagpur",
    latitude=21.1458,
    longitude=79.0882,
    country="India",
    admin1="Maharashtra",
    country_code="IN",
    display_name="Nagpur, Maharashtra, India"
)

# In-memory fast cache (TTL: 120 seconds)
_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

class WeatherService:
    def __init__(self):
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.timeout = 2.5

    async def search_location(self, query: str) -> List[LocationSearchResult]:
        """Search cities using Open-Meteo Geocoding API with fallback search."""
        query = query.strip()
        if not query:
            return [DEFAULT_LOCATION]

        cache_key = f"geo_{query.lower()}"
        now = time.time()
        if cache_key in _CACHE and now - _CACHE[cache_key][0] < 300:
            return _CACHE[cache_key][1]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(self.geocoding_url, params={
                    "name": query,
                    "count": 6,
                    "language": "en",
                    "format": "json"
                })
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    for item in data.get("results", []):
                        admin1 = item.get("admin1", "")
                        country = item.get("country", "")
                        display_parts = [item.get("name")]
                        if admin1:
                            display_parts.append(admin1)
                        if country:
                            display_parts.append(country)
                        display_name = ", ".join(display_parts)

                        results.append(LocationSearchResult(
                            id=item.get("id"),
                            name=item.get("name"),
                            latitude=round(item.get("latitude"), 4),
                            longitude=round(item.get("longitude"), 4),
                            country=country,
                            admin1=admin1,
                            country_code=item.get("country_code", ""),
                            display_name=display_name
                        ))
                    if results:
                        _CACHE[cache_key] = (now, results)
                        return results
        except Exception as e:
            logger.warning(f"Geocoding API error: {e}. Falling back to internal directory.")

        # Fallback local search
        matches = []
        for loc in POPULAR_CITIES:
            if query.lower() in loc["name"].lower() or query.lower() in loc["admin1"].lower():
                display = f"{loc['name']}, {loc['admin1']}, {loc['country']}"
                matches.append(LocationSearchResult(
                    name=loc["name"],
                    latitude=loc["latitude"],
                    longitude=loc["longitude"],
                    country=loc["country"],
                    admin1=loc["admin1"],
                    country_code=loc["country_code"],
                    display_name=display
                ))

        res_final = matches if matches else [
            LocationSearchResult(
                name=query.title(),
                latitude=DEFAULT_LOCATION.latitude,
                longitude=DEFAULT_LOCATION.longitude,
                country="India",
                admin1="Demo Region",
                country_code="IN",
                display_name=f"{query.title()}, India"
            )
        ]
        _CACHE[cache_key] = (now, res_final)
        return res_final

    async def _fetch_unified_forecast(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch current, hourly, and daily in a single HTTP request with caching."""
        cache_key = f"wx_{round(lat, 2)}_{round(lon, 2)}"
        now = time.time()
        if cache_key in _CACHE and (now - _CACHE[cache_key][0]) < 120:
            return _CACHE[cache_key][1]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure",
                    "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m,uv_index",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset,uv_index_max",
                    "timezone": "auto",
                    "forecast_days": 7
                }
                res = await client.get(self.forecast_url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    _CACHE[cache_key] = (now, data)
                    return data
        except Exception as e:
            logger.warning(f"Unified forecast fetch error: {e}")
        return None

    async def get_all_weather_data(
        self,
        lat: float,
        lon: float,
        location: Optional[LocationSearchResult] = None
    ) -> Tuple[CurrentWeatherResponse, HourlyForecastResponse, DailyForecastResponse]:
        """Convenience method to retrieve current, hourly, and daily responses in one call."""
        if not location:
            location = DEFAULT_LOCATION

        data = await self._fetch_unified_forecast(lat, lon)
        if data:
            curr_resp = self._parse_current(data, location)
            hourly_resp = self._parse_hourly(data, location)
            daily_resp = self._parse_daily(data, location)
            return curr_resp, hourly_resp, daily_resp

        # Fallback Demo Data
        return (
            self._generate_demo_current_weather(location),
            self._generate_demo_hourly(location),
            self._generate_demo_daily(location)
        )

    def _parse_current(self, data: Dict[str, Any], location: LocationSearchResult) -> CurrentWeatherResponse:
        curr = data.get("current", {})
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        code = curr.get("weather_code", 0)
        wmo = get_wmo_details(code)
        temp = round(curr.get("temperature_2m", 25.0), 1)
        feels = round(curr.get("apparent_temperature", temp), 1)
        humidity = int(curr.get("relative_humidity_2m", 60))
        wind_speed = round(curr.get("wind_speed_10m", 10.0), 1)
        wind_dir = curr.get("wind_direction_10m", 0)
        pressure = round(curr.get("surface_pressure", 1013.2), 1)
        is_day = curr.get("is_day", 1)

        rain_probs = hourly.get("precipitation_probability", [20])
        rain_prob = int(rain_probs[0]) if rain_probs else 0
        uv_indices = hourly.get("uv_index", [4.0])
        uv_index = float(uv_indices[0]) if uv_indices else 4.0

        sunrises = daily.get("sunrise", [])
        sunsets = daily.get("sunset", [])
        sunrise_str = format_iso_time(sunrises[0]) if sunrises else "06:05 AM"
        sunset_str = format_iso_time(sunsets[0]) if sunsets else "06:40 PM"

        comfort = calculate_comfort_level(temp, humidity, wind_speed)
        advice = self._generate_quick_advice(temp, rain_prob, code, wind_speed)

        current_obj = CurrentWeather(
            temperature=temp,
            feels_like=feels,
            humidity=humidity,
            wind_speed=wind_speed,
            wind_direction=wind_dir,
            rain_probability=rain_prob,
            weather_code=code,
            condition=wmo["condition"],
            icon=wmo["icon"],
            uv_index=uv_index,
            sunrise=sunrise_str,
            sunset=sunset_str,
            pressure=pressure,
            is_day=is_day,
            time=datetime.now().strftime("%I:%M %p"),
            comfort_level=comfort
        )

        return CurrentWeatherResponse(
            location=location,
            current=current_obj,
            smart_advice=advice,
            is_demo=False
        )

    def _parse_hourly(self, data: Dict[str, Any], location: LocationSearchResult) -> HourlyForecastResponse:
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        rain_probs = hourly.get("precipitation_probability", [])
        codes = hourly.get("weather_code", [])
        winds = hourly.get("wind_speed_10m", [])
        humidities = hourly.get("relative_humidity_2m", [])

        now_iso = datetime.now().strftime("%Y-%m-%dT%H:00")
        start_idx = 0
        for i, t in enumerate(times):
            if t >= now_iso:
                start_idx = i
                break

        items: List[HourlyForecastItem] = []
        for i in range(start_idx, min(start_idx + 24, len(times))):
            code = codes[i] if i < len(codes) else 0
            wmo = get_wmo_details(code)
            iso_t = times[i]
            hour_label = format_iso_time(iso_t)

            items.append(HourlyForecastItem(
                time=iso_t,
                hour_label=hour_label,
                temperature=round(temps[i], 1) if i < len(temps) else 25.0,
                rain_probability=int(rain_probs[i]) if i < len(rain_probs) else 0,
                weather_code=code,
                condition=wmo["condition"],
                icon=wmo["icon"],
                wind_speed=round(winds[i], 1) if i < len(winds) else 10.0,
                humidity=int(humidities[i]) if i < len(humidities) else 50
            ))

        return HourlyForecastResponse(location=location, hourly=items, is_demo=False)

    def _parse_daily(self, data: Dict[str, Any], location: LocationSearchResult) -> DailyForecastResponse:
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weather_code", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        rain_probs = daily.get("precipitation_probability_max", [])
        sunrises = daily.get("sunrise", [])
        sunsets = daily.get("sunset", [])
        uv_maxs = daily.get("uv_index_max", [])

        items: List[DailyForecastItem] = []
        for i in range(len(dates)):
            code = codes[i] if i < len(codes) else 0
            wmo = get_wmo_details(code)
            day_name, full_date = format_iso_date(dates[i])
            if i == 0:
                day_name = "Today"
            elif i == 1:
                day_name = "Tomorrow"

            items.append(DailyForecastItem(
                date=dates[i],
                day_name=day_name,
                full_date=full_date,
                min_temp=round(min_temps[i], 1) if i < len(min_temps) else 20.0,
                max_temp=round(max_temps[i], 1) if i < len(max_temps) else 30.0,
                rain_probability=int(rain_probs[i]) if i < len(rain_probs) else 10,
                weather_code=code,
                condition=wmo["condition"],
                icon=wmo["icon"],
                sunrise=format_iso_time(sunrises[i]) if i < len(sunrises) else "06:00 AM",
                sunset=format_iso_time(sunsets[i]) if i < len(sunsets) else "06:45 PM",
                uv_index_max=float(uv_maxs[i]) if i < len(uv_maxs) else 6.0
            ))

        return DailyForecastResponse(location=location, daily=items, is_demo=False)

    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        location: Optional[LocationSearchResult] = None
    ) -> CurrentWeatherResponse:
        curr, _, _ = await self.get_all_weather_data(lat, lon, location)
        return curr

    async def get_hourly_forecast(
        self,
        lat: float,
        lon: float,
        location: Optional[LocationSearchResult] = None
    ) -> HourlyForecastResponse:
        _, hourly, _ = await self.get_all_weather_data(lat, lon, location)
        return hourly

    async def get_daily_forecast(
        self,
        lat: float,
        lon: float,
        location: Optional[LocationSearchResult] = None
    ) -> DailyForecastResponse:
        _, _, daily = await self.get_all_weather_data(lat, lon, location)
        return daily

    def _generate_quick_advice(self, temp: float, rain_prob: int, code: int, wind_speed: float) -> str:
        if code in [95, 96, 99]:
            return "⚡ Active thunderstorm alert. Stay indoors and avoid open fields or trees."
        elif rain_prob >= 70 or code in [63, 65, 81, 82]:
            return "☔ High chance of heavy rain today. Carry an umbrella and plan travel accordingly."
        elif rain_prob >= 40 or code in [51, 53, 61, 80]:
            return "🌦️ Light rain showers expected. Keep rain gear handy if heading out."
        elif temp >= 38:
            return "☀️ High temperatures today. Stay well-hydrated and limit intense outdoor exposure between 12 PM - 4 PM."
        elif temp <= 14:
            return "🧥 Cool and crisp weather. Wear a jacket or layers for morning/evening commute."
        elif wind_speed > 28:
            return "💨 Gusty winds detected. Take caution while riding two-wheelers on open bridges/highways."
        else:
            return "🚲 Great weather conditions today! Ideal for outdoor activities, travel, and commuting."

    def _generate_demo_current_weather(self, location: LocationSearchResult) -> CurrentWeatherResponse:
        current_obj = CurrentWeather(
            temperature=28.4,
            feels_like=29.6,
            humidity=64,
            wind_speed=12.5,
            wind_direction=240,
            rain_probability=35,
            weather_code=2,
            condition="Partly Cloudy",
            icon="⛅",
            uv_index=5.8,
            sunrise="05:58 AM",
            sunset="06:38 PM",
            pressure=1012.4,
            is_day=1,
            time=datetime.now().strftime("%I:%M %p"),
            comfort_level="Ideal & Very Pleasant"
        )
        return CurrentWeatherResponse(
            location=location,
            current=current_obj,
            smart_advice="⛅ Pleasant partly cloudy skies in Nagpur. Light breeze, ideal for bike travel and outdoor work.",
            is_demo=True
        )

    def _generate_demo_hourly(self, location: LocationSearchResult) -> HourlyForecastResponse:
        hours = ["9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM"]
        temps = [26.0, 27.5, 29.0, 30.8, 31.5, 31.0, 29.8, 28.5, 27.2, 26.0, 25.1, 24.5]
        rain = [10, 15, 20, 30, 45, 60, 70, 50, 30, 20, 10, 5]
        codes = [1, 2, 2, 3, 51, 61, 63, 80, 2, 1, 0, 0]

        items = []
        for i in range(len(hours)):
            wmo = get_wmo_details(codes[i])
            items.append(HourlyForecastItem(
                time=f"2026-09-01T{9+i:02d}:00",
                hour_label=hours[i],
                temperature=temps[i],
                rain_probability=rain[i],
                weather_code=codes[i],
                condition=wmo["condition"],
                icon=wmo["icon"],
                wind_speed=12.0,
                humidity=60
            ))

        return HourlyForecastResponse(location=location, hourly=items, is_demo=True)

    def _generate_demo_daily(self, location: LocationSearchResult) -> DailyForecastResponse:
        days = ["Today", "Tomorrow", "Thu", "Fri", "Sat", "Sun", "Mon"]
        dates = ["Sep 01", "Sep 02", "Sep 03", "Sep 04", "Sep 05", "Sep 06", "Sep 07"]
        maxs = [31.5, 30.0, 29.0, 32.0, 33.5, 32.8, 31.0]
        mins = [23.0, 22.5, 21.8, 23.2, 24.0, 23.5, 22.8]
        rain = [35, 75, 60, 20, 10, 15, 40]
        codes = [2, 63, 61, 1, 0, 1, 80]

        items = []
        for i in range(7):
            wmo = get_wmo_details(codes[i])
            items.append(DailyForecastItem(
                date=f"2026-09-{i+1:02d}",
                day_name=days[i],
                full_date=dates[i],
                min_temp=mins[i],
                max_temp=maxs[i],
                rain_probability=rain[i],
                weather_code=codes[i],
                condition=wmo["condition"],
                icon=wmo["icon"],
                sunrise="05:58 AM",
                sunset="06:38 PM",
                uv_index_max=6.5
            ))

        return DailyForecastResponse(location=location, daily=items, is_demo=True)

weather_service = WeatherService()
