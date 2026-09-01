import uuid
from typing import List, Optional
from backend.models.schemas import SmartAlert, AlertsResponse, LocationSearchResult
from backend.services.weather_service import weather_service, DEFAULT_LOCATION

class AlertService:
    async def evaluate_alerts(
        self,
        lat: float,
        lon: float,
        location: Optional[LocationSearchResult] = None
    ) -> AlertsResponse:
        """Evaluate real-time forecast data to detect severe weather alerts."""
        if not location:
            location = DEFAULT_LOCATION

        alerts: List[SmartAlert] = []
        is_demo = False

        try:
            curr_resp, hourly_resp, daily_resp = await weather_service.get_all_weather_data(lat, lon, location)
            is_demo = curr_resp.is_demo

            # 1. Check for Heavy Rain / Thunderstorms in Hourly & Daily
            for item in hourly_resp.hourly[:24]:
                if item.weather_code in [95, 96, 99]:
                    alerts.append(SmartAlert(
                        id=f"alert-storm-{uuid.uuid4().hex[:6]}",
                        type="thunderstorm",
                        severity="critical",
                        title="Active Thunderstorm Warning",
                        message=f"Severe thunderstorm activity and lightning predicted near {location.name} around {item.hour_label}.",
                        expected_time=f"Today around {item.hour_label}",
                        location=location.display_name,
                        recommended_action="Seek sturdy indoor shelter, unplug sensitive electronics, and avoid tall trees or open grounds.",
                        icon="⚡"
                    ))
                    break

            # Daily rain check for tomorrow
            if len(daily_resp.daily) > 1:
                tomorrow_item = daily_resp.daily[1]
                if tomorrow_item.rain_probability >= 60 or tomorrow_item.weather_code in [63, 65, 81, 82]:
                    alerts.append(SmartAlert(
                        id=f"alert-rain-{uuid.uuid4().hex[:6]}",
                        type="heavy_rain",
                        severity="warning" if tomorrow_item.rain_probability < 80 else "critical",
                        title="Heavy Rain Forecast Tomorrow",
                        message=f"High chance of sustained rainfall ({tomorrow_item.rain_probability}%) expected in {location.name}.",
                        expected_time="Tomorrow Afternoon to Evening",
                        location=location.display_name,
                        recommended_action="Carry a durable umbrella or raincoat. Avoid low-lying waterlogged roads and allow extra commute time.",
                        icon="🌧️"
                    ))

            # 2. Check for Heatwave / Extreme Temperature
            max_temp = max([d.max_temp for d in daily_resp.daily[:2]], default=curr_resp.current.temperature)
            if max_temp >= 41.0:
                alerts.append(SmartAlert(
                    id=f"alert-heat-{uuid.uuid4().hex[:6]}",
                    type="heatwave",
                    severity="critical",
                    title="Extreme Heat Alert (IMD Heatwave Level)",
                    message=f"Temperatures soaring to {max_temp}°C in {location.name}. High risk of dehydration and heat exhaustion.",
                    expected_time="12:00 PM to 4:30 PM",
                    location=location.display_name,
                    recommended_action="Stay indoors during peak sunshine, drink electrolyte fluids, and wear loose light-colored cotton clothing.",
                    icon="☀️"
                ))
            elif max_temp >= 38.0:
                alerts.append(SmartAlert(
                    id=f"alert-heat-{uuid.uuid4().hex[:6]}",
                    type="high_temp",
                    severity="warning",
                    title="High Temperature Advisory",
                    message=f"Maximum temperature expected to reach {max_temp}°C.",
                    expected_time="Mid-day to Afternoon",
                    location=location.display_name,
                    recommended_action="Keep water handy, take periodic breaks in shaded areas, and apply sunscreen.",
                    icon="🌡️"
                ))

            # 3. Check for Strong Winds
            if curr_resp.current.wind_speed >= 32.0:
                alerts.append(SmartAlert(
                    id=f"alert-wind-{uuid.uuid4().hex[:6]}",
                    type="strong_wind",
                    severity="warning",
                    title="High Wind Velocity Advisory",
                    message=f"Sustained wind gusts reaching {curr_resp.current.wind_speed} km/h.",
                    expected_time="Currently active",
                    location=location.display_name,
                    recommended_action="Secure loose outdoor fixtures, exercise caution on two-wheelers on elevated highways.",
                    icon="💨"
                ))

            # 4. Check for UV Index
            if curr_resp.current.uv_index >= 8.0:
                alerts.append(SmartAlert(
                    id=f"alert-uv-{uuid.uuid4().hex[:6]}",
                    type="high_uv",
                    severity="info",
                    title="Very High UV Radiation",
                    message=f"UV Index reading of {curr_resp.current.uv_index} (Very High).",
                    expected_time="11:00 AM - 3:00 PM",
                    location=location.display_name,
                    recommended_action="Use UV-blocking sunglasses, SPF 30+ sunscreen, and protective headwear.",
                    icon="🧴"
                ))

        except Exception:
            is_demo = True

        # If no hazardous alerts exist, provide an informative all-clear alert
        if not alerts:
            alerts.append(SmartAlert(
                id=f"alert-clear-{uuid.uuid4().hex[:6]}",
                type="favorable",
                severity="info",
                title="Stable Weather Conditions",
                message=f"No hazardous weather alerts currently active for {location.name}. Weather is favorable.",
                expected_time="Next 24 Hours",
                location=location.display_name,
                recommended_action="Conditions are suitable for daily commuting, outdoor sports, and travel.",
                icon="✅"
            ))

        return AlertsResponse(
            location=location,
            alerts=alerts,
            total_active=len([a for a in alerts if a.severity in ["warning", "critical"]]),
            is_demo=is_demo
        )

alert_service = AlertService()
