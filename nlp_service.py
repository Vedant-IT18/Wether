import os
import re
import httpx
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from backend.models.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    SmartAlert,
    LocationSearchResult
)
from backend.services.weather_service import weather_service, DEFAULT_LOCATION
from backend.services.alert_service import alert_service
from backend.services.climate_service import climate_service

logger = logging.getLogger("nlp_service")

class NLPService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    def classify_intent(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Classify user query into intent and extracted entities using robust regex/heuristics."""
        lower = text.lower().strip()
        entities = {
            "time_target": "today",
            "time_of_day": "all_day",
            "activity": None,
            "transport": None
        }

        # Time extraction
        if "tomorrow" in lower:
            entities["time_target"] = "tomorrow"
        elif "tonight" in lower or "this night" in lower:
            entities["time_target"] = "tonight"
            entities["time_of_day"] = "night"
        elif "this evening" in lower or "evening" in lower:
            entities["time_of_day"] = "evening"
        elif "morning" in lower:
            entities["time_of_day"] = "morning"
        elif "afternoon" in lower:
            entities["time_of_day"] = "afternoon"
        elif "week" in lower or "7 day" in lower:
            entities["time_target"] = "week"

        # Transport & Activity extraction
        if "bike" in lower or "motorcycle" in lower or "scooter" in lower or "two wheeler" in lower:
            entities["transport"] = "bike"
        elif "car" in lower or "drive" in lower:
            entities["transport"] = "car"
        elif "walk" in lower or "walking" in lower or "pedestrian" in lower:
            entities["transport"] = "walk"

        if "run" in lower or "running" in lower or "jog" in lower:
            entities["activity"] = "running"
        elif "cricket" in lower or "football" in lower or "match" in lower or "play" in lower:
            entities["activity"] = "outdoor_sports"
        elif "picnic" in lower or "outing" in lower or "hangout" in lower:
            entities["activity"] = "picnic"
        elif "outdoor" in lower or "outside" in lower:
            entities["activity"] = "outdoor_general"

        # Intent classification rules
        if any(w in lower for w in ["why is this month hotter", "hotter this month", "climate change", "global warming", "climate insight", "historical trend", "temperature trend", "why hotter"]):
            return "climate_insight", entities

        if any(w in lower for w in ["alert", "warning", "danger", "hazard", "heavy rain alert", "storm alert", "safe"]):
            return "alerts", entities

        if any(w in lower for w in ["bike", "travel", "ride", "drive", "road trip", "commute", "traffic"]):
            return "travel_advice", entities

        if any(w in lower for w in ["running", "jogging", "cricket", "outdoor", "outside", "sport", "event", "picnic", "hike"]):
            return "outdoor_activity", entities

        if any(w in lower for w in ["rain", "raining", "rainfall", "umbrella", "shower", "drizzle", "wet", "precipitation"]):
            return "rainfall", entities

        if any(w in lower for w in ["temperature", "temp", "how hot", "how cold", "degrees", "celsius"]):
            return "temperature", entities

        if any(w in lower for w in ["wear", "clothes", "clothing", "jacket", "sweater", "dress"]):
            return "clothing_advice", entities

        if any(w in lower for w in ["forecast", "7 day", "weekly", "hourly", "upcoming"]):
            return "forecast", entities

        if "tomorrow" in lower:
            return "tomorrow_weather", entities

        if any(w in lower for w in ["hi", "hello", "hey", "who are you", "what can you do", "help"]):
            return "greeting", entities

        return "current_weather", entities

    async def process_chat(self, req: ChatMessageRequest) -> ChatMessageResponse:
        """Main chat orchestration pipeline."""
        raw_msg = req.message.strip()
        if not raw_msg:
            return ChatMessageResponse(
                answer="Please enter a weather or climate question, e.g., *'Will it rain tomorrow?'* or *'Should I travel by bike today?'*",
                intent="empty",
                suggestions=["Will it rain tomorrow?", "Should I travel by bike today?", "Why is this month hotter?"],
                timestamp=datetime.now().strftime("%I:%M %p")
            )

        # 1. Resolve Location
        location = await self._resolve_location(req)

        # 2. Extract Intent & Entities
        intent, entities = self.classify_intent(raw_msg)

        # 3. Try LLM if API Key is configured
        if self.openai_api_key or self.groq_api_key:
            try:
                llm_res = await self._query_llm(raw_msg, location, intent, entities)
                if llm_res:
                    return llm_res
            except Exception as e:
                logger.warning(f"LLM API query failed: {e}. Falling back to rule-based NLP.")

        # 4. Built-in Heuristic / Rule-based NLP Engine (Reliable SIH Zero-Dependency Fallback)
        return await self._generate_rule_based_response(raw_msg, location, intent, entities)

    async def _resolve_location(self, req: ChatMessageRequest) -> LocationSearchResult:
        """Resolve location from coordinates or text name."""
        if req.latitude is not None and req.longitude is not None:
            return LocationSearchResult(
                name=req.location or "Selected Location",
                latitude=req.latitude,
                longitude=req.longitude,
                country="India",
                admin1="",
                country_code="IN",
                display_name=req.location or "Your Location"
            )

        loc_query = req.location or "Nagpur"
        results = await weather_service.search_location(loc_query)
        return results[0] if results else DEFAULT_LOCATION

    async def _generate_rule_based_response(
        self,
        query: str,
        loc: LocationSearchResult,
        intent: str,
        entities: Dict[str, Any]
    ) -> ChatMessageResponse:
        """Generate concise, actionable, SIH presentation-grade structured AI response."""
        now_time = datetime.now().strftime("%I:%M %p")

        # Fetch required meteorological datasets in a single cached call
        curr_data, hourly_data, daily_data = await weather_service.get_all_weather_data(loc.latitude, loc.longitude, loc)
        alerts_data = await alert_service.evaluate_alerts(loc.latitude, loc.longitude, loc)

        c = curr_data.current
        tomorrow_item = daily_data.daily[1] if len(daily_data.daily) > 1 else daily_data.daily[0]
        today_item = daily_data.daily[0]

        top_alert = alerts_data.alerts[0] if alerts_data.alerts and alerts_data.alerts[0].severity in ["warning", "critical"] else None

        default_suggestions = [
            "Will it rain tomorrow?",
            "Should I travel by bike today?",
            "Why is this month hotter?",
            "What will the temperature be tomorrow?",
            "Any active weather alerts?"
        ]

        # --- INTENT 1: Rainfall Query ---
        if intent == "rainfall":
            target = entities["time_target"]
            time_of_day = entities["time_of_day"]

            if target == "tomorrow":
                rain_prob = tomorrow_item.rain_probability
                cond = tomorrow_item.condition
                period_str = "tomorrow evening" if time_of_day in ["evening", "all_day"] else f"tomorrow {time_of_day}"

                if rain_prob >= 60:
                    ans = (
                        f"🌧️ **High chance of rainfall ({rain_prob}%)** {period_str} in **{loc.name}**.\n\n"
                        f"📍 **Location:** {loc.display_name}\n"
                        f"🕒 **Expected Period:** {period_str.title()}\n"
                        f"☔ **Rain Probability:** {rain_prob}%\n"
                        f"🌡️ **Temperature:** {tomorrow_item.max_temp}°C (High) / {tomorrow_item.min_temp}°C (Low)\n\n"
                        f"💡 **Advice:** Carry an umbrella or raincoat. If you are planning outdoor activities, consider completing them earlier in the day."
                    )
                    advice = f"☔ Rain probability is {rain_prob}% tomorrow. Keep rain gear handy."
                elif rain_prob >= 30:
                    ans = (
                        f"🌦️ **Moderate chance of light showers ({rain_prob}%)** {period_str} in **{loc.name}**.\n\n"
                        f"📍 **Location:** {loc.display_name}\n"
                        f"🕒 **Expected Period:** {period_str.title()}\n"
                        f"☔ **Rain Probability:** {rain_prob}%\n\n"
                        f"💡 **Advice:** Scattered drizzle is possible. A compact umbrella is recommended."
                    )
                    advice = "🌦️ Light showers possible. Keep a lightweight jacket or umbrella handy."
                else:
                    ans = (
                        f"☀️ **Low probability of rain ({rain_prob}%)** {period_str} in **{loc.name}**.\n\n"
                        f"📍 **Location:** {loc.display_name}\n"
                        f"🕒 **Expected Period:** {period_str.title()}\n"
                        f"☁️ **Condition:** {cond}\n"
                        f"☔ **Rain Probability:** {rain_prob}%\n\n"
                        f"💡 **Advice:** Clear and dry weather expected. No umbrella required for tomorrow."
                    )
                    advice = "☀️ Dry conditions expected tomorrow. Great for outdoor plans."

            else:
                rain_prob = c.rain_probability
                if rain_prob >= 50:
                    ans = (
                        f"🌧️ **Rain is likely today ({rain_prob}%)** in **{loc.name}**.\n\n"
                        f"📍 **Location:** {loc.display_name}\n"
                        f"💧 **Current Humidity:** {c.humidity}%\n"
                        f"☔ **Precipitation Chance:** {rain_prob}%\n"
                        f"☁️ **Current Sky:** {c.condition} {c.icon}\n\n"
                        f"💡 **Advice:** Keep rain protection with you when stepping out today."
                    )
                    advice = "☔ High rain probability today. Carry an umbrella."
                else:
                    ans = (
                        f"🌤️ **Low chance of rain today ({rain_prob}%)** in **{loc.name}**.\n\n"
                        f"📍 **Location:** {loc.display_name}\n"
                        f"🌡️ **Current Temp:** {c.temperature}°C (Feels like {c.feels_like}°C)\n"
                        f"☁️ **Sky:** {c.condition} {c.icon}\n"
                        f"☔ **Rain Probability:** {rain_prob}%\n\n"
                        f"💡 **Advice:** Weather is predominantly dry today. Enjoy your day!"
                    )
                    advice = "🌤️ Minimal chance of rain today. Good for travel."

            return ChatMessageResponse(
                answer=ans,
                intent=intent,
                advice=advice,
                alert=top_alert,
                weather_data={"temperature": c.temperature, "rain_probability": c.rain_probability, "condition": c.condition},
                suggestions=["Should I travel by bike today?", "What will the temperature be tomorrow?", "Why is this month hotter?"],
                timestamp=now_time
            )

        # --- INTENT 2: Travel & Bike Advice ---
        elif intent == "travel_advice":
            transport = entities["transport"] or "bike"
            target = entities["time_target"]

            if transport == "bike":
                if c.rain_probability >= 60 or c.weather_code in [63, 65, 81, 82, 95]:
                    ans = (
                        f"⚠️ **Bike Travel Caution for {loc.name}**\n\n"
                        f"🚲 **Bike Feasibility:** Risky / Not Recommended during peak rain.\n"
                        f"🌧️ **Reason:** High rainfall probability ({c.rain_probability}%) and slippery road conditions.\n"
                        f"💨 **Wind Speed:** {c.wind_speed} km/h\n"
                        f"📍 **Location:** {loc.display_name}\n\n"
                        f"💡 **Advice:** If you must ride your two-wheeler, wear a high-visibility raincoat, check tyre grip, reduce speed, and avoid water-logged underpasses."
                    )
                    advice = "🚲 Heavy rain expected. Avoid bike travel if possible or wear full rain gear."
                elif c.wind_speed > 28:
                    ans = (
                        f"💨 **Moderate Bike Travel Advisory for {loc.name}**\n\n"
                        f"🚲 **Bike Feasibility:** Moderate - Caution needed.\n"
                        f"💨 **Wind Speed:** {c.wind_speed} km/h (Gusty conditions)\n"
                        f"🌡️ **Temperature:** {c.temperature}°C\n\n"
                        f"💡 **Advice:** Strong crosswinds may affect two-wheeler balance on open highways and flyovers. Maintain safe speed."
                    )
                    advice = "💨 Gusty winds. Maintain two-wheeler stability on open roads."
                else:
                    ans = (
                        f"🚲 **Bike Travel is Recommended for {loc.name} Today!**\n\n"
                        f"✅ **Feasibility:** Excellent & Safe\n"
                        f"🌡️ **Temperature:** {c.temperature}°C (Feels like {c.feels_like}°C)\n"
                        f"🌤️ **Sky Condition:** {c.condition} {c.icon}\n"
                        f"☔ **Rain Probability:** {c.rain_probability}%\n"
                        f"💨 **Wind Speed:** {c.wind_speed} km/h (Gentle breeze)\n\n"
                        f"💡 **Advice:** Weather conditions are suitable for bike travel today. Keep an eye on the evening sky if traveling late."
                    )
                    advice = "🚲 Weather is favorable for bike travel and outdoor commuting."
            else:
                ans = (
                    f"🚗 **Travel Advisory for {loc.name}**\n\n"
                    f"📍 **Location:** {loc.display_name}\n"
                    f"🌡️ **Current Weather:** {c.temperature}°C, {c.condition} {c.icon}\n"
                    f"☔ **Rain Probability:** {c.rain_probability}%\n"
                    f"💨 **Wind:** {c.wind_speed} km/h | 💧 **Humidity:** {c.humidity}%\n\n"
                    f"💡 **Advice:** Overall road conditions are favorable. Ensure standard vehicular checks."
                )
                advice = "🚗 Good driving conditions across the city today."

            return ChatMessageResponse(
                answer=ans,
                intent=intent,
                advice=advice,
                alert=top_alert,
                weather_data={"temperature": c.temperature, "wind_speed": c.wind_speed, "rain_probability": c.rain_probability},
                suggestions=["Will it rain tomorrow?", "Why is this month hotter?", "What's the weather this evening?"],
                timestamp=now_time
            )

        # --- INTENT 3: Climate Insight / Why Hotter ---
        elif intent == "climate_insight":
            insight = await climate_service.get_climate_insights(loc.latitude, loc.longitude, loc)
            ans = (
                f"🌍 **Climate Insight: {insight.headline}**\n\n"
                f"{insight.summary}\n\n"
                f"📊 **Key Meteorological Factors:**\n"
                f"• **Temperature Anomaly:** {insight.anomaly_c}°C relative to the 10-year baseline\n"
                f"• **Rainfall Variation:** {insight.rainfall_anomaly_pct}%\n\n"
                f"💡 **Scientific Explanation:**\n"
                f"{insight.explanation}\n\n"
                f"*(Note: Based on available historical reanalysis datasets for {loc.name}.)*"
            )
            advice = f"🌍 Temperature is running {insight.anomaly_c}°C above long-term normal in {loc.name}."

            return ChatMessageResponse(
                answer=ans,
                intent=intent,
                advice=advice,
                alert=top_alert,
                weather_data={"anomaly": insight.anomaly_c, "current_temp": c.temperature},
                suggestions=["Will it rain tomorrow?", "Should I travel by bike today?", "Show 7-day forecast"],
                timestamp=now_time
            )

        # --- INTENT 4: Tomorrow Weather / Temperature ---
        elif intent in ["tomorrow_weather", "temperature"]:
            if "tomorrow" in query.lower():
                ans = (
                    f"📅 **Tomorrow's Weather Forecast for {loc.name}**\n\n"
                    f"📍 **Location:** {loc.display_name}\n"
                    f"🌡️ **Expected High:** {tomorrow_item.max_temp}°C\n"
                    f"❄️ **Expected Low:** {tomorrow_item.min_temp}°C\n"
                    f"☁️ **Condition:** {tomorrow_item.condition} {tomorrow_item.icon}\n"
                    f"☔ **Rain Probability:** {tomorrow_item.rain_probability}%\n"
                    f"🌅 **Sunrise / Sunset:** {tomorrow_item.sunrise} / {tomorrow_item.sunset}\n\n"
                    f"💡 **Advice:** " + ("Carry rain gear as precipitation is likely." if tomorrow_item.rain_probability >= 50 else "Pleasant temperature range expected for work and travel.")
                )
                advice = f"📅 Tomorrow: {tomorrow_item.min_temp}°C - {tomorrow_item.max_temp}°C, {tomorrow_item.condition}."
            else:
                ans = (
                    f"🌡️ **Temperature Overview for {loc.name}**\n\n"
                    f"📍 **Location:** {loc.display_name}\n"
                    f"🌡️ **Current Temperature:** {c.temperature}°C\n"
                    f"🤔 **Feels Like:** {c.feels_like}°C\n"
                    f"📈 **Today's Max:** {today_item.max_temp}°C\n"
                    f"📉 **Today's Min:** {today_item.min_temp}°C\n"
                    f"💧 **Humidity:** {c.humidity}% | 💨 **Wind:** {c.wind_speed} km/h\n\n"
                    f"💡 **Assessment:** {c.comfort_level}."
                )
                advice = f"🌡️ Currently {c.temperature}°C (Feels like {c.feels_like}°C) in {loc.name}."

            return ChatMessageResponse(
                answer=ans,
                intent=intent,
                advice=advice,
                alert=top_alert,
                weather_data={"temperature": c.temperature, "feels_like": c.feels_like},
                suggestions=["Will it rain tomorrow?", "Should I travel by bike today?", "Why is this month hotter?"],
                timestamp=now_time
            )

        # --- INTENT 5: Outdoor Activity / Sports ---
        elif intent == "outdoor_activity":
            act = entities["activity"] or "outdoor sports"
            target = entities["time_target"]

            item = tomorrow_item if target == "tomorrow" else today_item
            rain_val = item.rain_probability

            if rain_val >= 60:
                ans = (
                    f"🏃 **Outdoor Activity Assessment: Not Ideal ({rain_val}% Rain Risk)**\n\n"
                    f"📍 **Location:** {loc.display_name}\n"
                    f"🎯 **Target Window:** {target.title()}\n"
                    f"🌧️ **Precipitation Chance:** {rain_val}%\n"
                    f"🌡️ **Expected Temp:** {item.min_temp}°C - {item.max_temp}°C\n\n"
                    f"💡 **Advice:** Ground surfaces may be damp and rain interruptions are likely. Consider indoor training or schedule activities early morning."
                )
                advice = f"🏃 Rain risk ({rain_val}%) for outdoor activities {target}."
            else:
                ans = (
                    f"🏃 **Outdoor Activity Assessment: Highly Favorable!**\n\n"
                    f"📍 **Location:** {loc.display_name}\n"
                    f"🎯 **Target Window:** {target.title()}\n"
                    f"🌤️ **Sky:** {item.condition} {item.icon}\n"
                    f"☔ **Rain Probability:** {rain_val}%\n"
                    f"🌡️ **Temperature Range:** {item.min_temp}°C to {item.max_temp}°C\n\n"
                    f"💡 **Advice:** Great conditions for running, cycling, cricket, and outdoor fitness. Morning hours (6 AM - 9 AM) offer peak freshness."
                )
                advice = f"🏃 Great conditions for outdoor sports and workouts {target}."

            return ChatMessageResponse(
                answer=ans,
                intent=intent,
                advice=advice,
                alert=top_alert,
                suggestions=["Will it rain tomorrow?", "Should I travel by bike today?", "Any active weather alerts?"],
                timestamp=now_time
            )

        # --- INTENT 6: Active Alerts ---
        elif intent == "alerts":
            active_list = alerts_data.alerts
            alert_texts = []
            for a in active_list:
                alert_texts.append(f"{a.icon} **{a.title}** ({a.severity.upper()})\n• Time: {a.expected_time}\n• Details: {a.message}\n• Action: {a.recommended_action}")

            ans = (
                f"⚠️ **Active Weather Alerts for {loc.name}**\n\n"
                + "\n\n".join(alert_texts)
            )
            advice = active_list[0].recommended_action if active_list else "All clear."

            return ChatMessageResponse(
                answer=ans,
                intent=intent,
                advice=advice,
                alert=top_alert,
                suggestions=["Will it rain tomorrow?", "Should I travel by bike today?", "Why is this month hotter?"],
                timestamp=now_time
            )

        # --- INTENT 7: Clothing Advice ---
        elif intent == "clothing_advice":
            temp = c.temperature
            if temp >= 32:
                ans = (
                    f"👕 **Clothing Recommendation for {loc.name} ({temp}°C)**\n\n"
                    f"• Light, breathable cotton or linen fabrics\n"
                    f"• Light colors to reflect sunlight\n"
                    f"• Sunglasses and cap for UV protection\n"
                    f"• Carry water to maintain hydration"
                )
            elif temp <= 18:
                ans = (
                    f"🧥 **Clothing Recommendation for {loc.name} ({temp}°C)**\n\n"
                    f"• Layered clothing: light jacket or sweater\n"
                    f"• Long sleeve shirts\n"
                    f"• Scarf for early morning / late evening commute"
                )
            else:
                ans = (
                    f"👔 **Clothing Recommendation for {loc.name} ({temp}°C)**\n\n"
                    f"• Standard comfortable daily wear\n"
                    f"• Casual or semi-formal cotton attire\n"
                    f"• Carry a light umbrella if rain probability rises above 40%"
                )
            advice = f"👕 Comfortable clothing recommended for {temp}°C in {loc.name}."
            return ChatMessageResponse(
                answer=ans,
                intent=intent,
                advice=advice,
                alert=top_alert,
                suggestions=["Will it rain tomorrow?", "Should I travel by bike today?", "Why is this month hotter?"],
                timestamp=now_time
            )

        # --- INTENT 8: Greeting / Intro ---
        elif intent == "greeting":
            ans = (
                f"👋 **Hello! I am WeatherGPT**, your conversational AI weather and climate companion for **Smart India Hackathon 2026**.\n\n"
                f"I can help you with:\n"
                f"• 🌧️ Natural language rain and storm forecasts (*'Will it rain tomorrow evening?'*)\n"
                f"• 🚲 Smart travel & commuting recommendations (*'Should I travel by bike today?'*)\n"
                f"• 🌍 Climate change insights & temperature trend analysis (*'Why is this month hotter?'*)\n"
                f"• ⚠️ Localized severe weather alerts & safety precautions\n\n"
                f"Currently viewing weather for **{loc.display_name}** ({c.temperature}°C, {c.condition}). How can I assist you today?"
            )
            return ChatMessageResponse(
                answer=ans,
                intent=intent,
                advice="Ask any question in plain English or choose a suggested topic below.",
                alert=top_alert,
                suggestions=default_suggestions,
                timestamp=now_time
            )

        # --- DEFAULT: Current Weather Overview ---
        else:
            ans = (
                f"🌤️ **Current Weather in {loc.name}**\n\n"
                f"📍 **Location:** {loc.display_name}\n"
                f"🌡️ **Temperature:** {c.temperature}°C (Feels like {c.feels_like}°C)\n"
                f"☁️ **Condition:** {c.condition} {c.icon}\n"
                f"💧 **Humidity:** {c.humidity}% | 💨 **Wind:** {c.wind_speed} km/h\n"
                f"☔ **Rain Probability:** {c.rain_probability}%\n"
                f"🌅 **Sunrise:** {c.sunrise} | 🌇 **Sunset:** {c.sunset}\n\n"
                f"💡 **Smart Advice:** {curr_data.smart_advice}"
            )
            return ChatMessageResponse(
                answer=ans,
                intent="current_weather",
                advice=curr_data.smart_advice,
                alert=top_alert,
                weather_data={"temperature": c.temperature, "condition": c.condition, "humidity": c.humidity},
                suggestions=default_suggestions,
                timestamp=now_time
            )

    async def _query_llm(
        self,
        query: str,
        loc: LocationSearchResult,
        intent: str,
        entities: Dict[str, Any]
    ) -> Optional[ChatMessageResponse]:
        """Optional LLM connector when API key is present."""
        api_key = self.openai_api_key or self.groq_api_key
        url = "https://api.openai.com/v1/chat/completions" if self.openai_api_key else "https://api.groq.com/openai/v1/chat/completions"
        model = "gpt-4o-mini" if self.openai_api_key else "llama-3.1-70b-versatile"

        curr_data, _, _ = await weather_service.get_all_weather_data(loc.latitude, loc.longitude, loc)
        c = curr_data.current

        system_prompt = (
            "You are WeatherGPT, an expert AI weather and climate assistant for Smart India Hackathon 2026. "
            "Provide concise, friendly, personalized and actionable responses in Markdown. "
            "Include bullet points for key numbers (Temperature, Rain %, Wind, Location) and a dedicated '💡 Advice:' section. "
            "Keep responses under 120 words."
        )

        user_content = (
            f"Location: {loc.display_name}\n"
            f"Current Weather: {c.temperature}°C, Feels like {c.feels_like}°C, {c.condition}, Humidity {c.humidity}%, Wind {c.wind_speed} km/h, Rain Chance {c.rain_probability}%\n"
            f"User Question: {query}"
        )

        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 250
                }
            )
            if res.status_code == 200:
                data = res.json()
                text = data["choices"][0]["message"]["content"]
                return ChatMessageResponse(
                    answer=text,
                    intent=intent,
                    advice=curr_data.smart_advice,
                    weather_data={"temperature": c.temperature, "condition": c.condition},
                    suggestions=["Will it rain tomorrow?", "Should I travel by bike today?", "Why is this month hotter?"],
                    timestamp=datetime.now().strftime("%I:%M %p")
                )
        return None

nlp_service = NLPService()
