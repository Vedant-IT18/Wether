# 🌦️ WeatherGPT: Conversational AI for Weather Forecasting, Alerts & Climate Information

> **Smart India Hackathon (SIH 2026) Prototype**  
> *A cutting-edge conversational weather intelligence assistant that translates meteorological data into actionable, personalized decisions.*

---

## 📌 1. Project Overview

**WeatherGPT** empowers users to interact with weather forecasting and climate data through natural language. Instead of deciphering complex meteorological charts and tables, users can simply ask questions like:
- *"Will it rain tomorrow evening?"*
- *"Should I travel by bike today?"*
- *"Why is this month hotter than usual?"*
- *"Is tomorrow morning good for running?"*

WeatherGPT analyzes real-time meteorological observations, hourly precipitation forecasts, and multi-year climatological baselines to generate structured, actionable, and safety-focused responses.

---

## 🚀 2. Key Features

| Feature | Description |
| :--- | :--- |
| 💬 **Conversational AI Interface** | Natural language intent recognition with entity extraction (timeframe, transport, activity). |
| 📍 **Smart Location Intelligence** | Instant city geocoding, autocomplete search, and one-click GPS auto-detection. |
| 🌦️ **Live Weather Dashboard** | Real-time temperature, feels-like, comfort index, humidity, wind, UV index, and sunrise/sunset. |
| 💡 **Smart Weather Advice** | Dynamic, contextual advice for daily commuting, outdoor activities, and clothing recommendations. |
| ⚠️ **Smart Hazard Alerts** | Meteorological threshold evaluator for heavy rainfall, thunderstorms, heatwaves, and strong winds with browser push notifications. |
| 📅 **Hourly & 7-Day Forecast** | Interactive 24-hour horizontal forecast cards and 7-day extended outlook. |
| 🌍 **Climate Insights & Trends** | Interactive Chart.js comparative analysis comparing current observations against 10-year climatological normals. |
| 🛡️ **Zero-Dependency Resilience** | 100% operational offline/demo fallback mode to guarantee flawless hackathon jury evaluation. |
| 🎙️ **Voice AI Support** | Integrated Speech Recognition (voice input) and Speech Synthesis (voice read-out). |

---

## 🛠️ 3. Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, HTTPX, Pydantic v2, Python-Dotenv
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism design system), JavaScript (ES6+), Chart.js
- **Weather Provider**: Open-Meteo API (Free, global reanalysis, zero API-key requirement)
- **AI/NLP Engine**: Multi-tier architecture with an advanced heuristic/rule-based NLP engine and pluggable LLM connectors (OpenAI / Groq / Gemini).

---

## 📁 4. Project Architecture

```
weathergpt/
│
├── backend/
│   ├── main.py                     # FastAPI application entry & static file server
│   ├── models/
│   │   └── schemas.py              # Pydantic data validation schemas
│   ├── routes/
│   │   ├── weather.py              # /api/weather/current, /hourly, /forecast, /alerts
│   │   ├── chat.py                 # /api/chat (conversational NLP pipeline)
│   │   ├── climate.py              # /api/climate/insights (historical anomaly)
│   │   ├── location.py             # /api/location/search (geocoding)
│   │   └── health.py               # /api/health (system status)
│   ├── services/
│   │   ├── weather_service.py      # Open-Meteo API connector & fallback mock
│   │   ├── nlp_service.py          # Intent classification & response synthesis
│   │   ├── alert_service.py        # Weather risk evaluator
│   │   └── climate_service.py      # Climate baseline & anomaly calculator
│   └── utils/
│       └── helpers.py              # WMO code mappings, formatting helpers
│
├── frontend/
│   ├── index.html                  # Responsive modern AI dashboard UI
│   ├── style.css                   # Dark glassmorphism styling & animations
│   ├── script.js                   # Application state, Chart.js, API clients
│   └── assets/                     # Graphic resources
│
├── .env.example                    # Environment variable template
├── .env                            # Active environment configuration
├── requirements.txt                # Python backend dependencies
└── README.md                       # Documentation & demo script
```

---

## ⚡ 5. Installation & Setup

### Step 1: Clone or Navigate to the Workspace
```bash
cd "c:\Users\VEDANT WAGHMARE\OneDrive\Desktop\SIH"
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` (optional, defaults are already configured):
```bash
cp .env.example .env
```

### Step 4: Run the WeatherGPT Application
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 📡 6. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/weather/current?lat=...&lon=...` | Returns current weather, comfort index, and quick advice. |
| `GET` | `/api/weather/hourly?lat=...&lon=...` | Returns 24-hour hourly forecast with precipitation probabilities. |
| `GET` | `/api/weather/forecast?lat=...&lon=...` | Returns 7-day extended daily forecast. |
| `GET` | `/api/weather/alerts?lat=...&lon=...` | Returns evaluated severe weather alerts and safety advice. |
| `POST` | `/api/chat` | Main conversational NLP endpoint (`{ "message": "...", "location": "..." }`). |
| `GET` | `/api/climate/insights?lat=...&lon=...` | Returns temperature trend anomaly and 10-year baseline comparison. |
| `GET` | `/api/location/search?query=...` | Returns geocoded city suggestions. |
| `GET` | `/api/health` | System health check. |

---

## 🏆 7. SIH 2026 Jury Demonstration Flow (< 2 Minutes)

1. **Step 1: Open Application**
   - Visit `http://127.0.0.1:8000`. Observe the modern AI startup glassmorphic theme, live clock, and default location (**Nagpur**).
2. **Step 2: Change Location**
   - Click on the search bar, type `Mumbai` or `New Delhi`, and select it. Observe instantaneous update across the hero card, 24h hourly carousel, 7-day forecast, and climate chart.
3. **Step 3: Natural Language Rain Query**
   - Click the prompt chip or type:  
     `"Will it rain tomorrow?"`  
     *WeatherGPT returns expected rain probability, timeframe, and umbrella/outdoor advice.*
4. **Step 4: Smart Travel Decision Query**
   - Type or click:  
     `"Should I travel by bike today?"`  
     *WeatherGPT evaluates wind speed, rain probability, and road conditions to provide safety advice.*
5. **Step 5: Climate Insight Query**
   - Type:  
     `"Why is this month hotter?"`  
     *WeatherGPT explains the meteorological factors and directs attention to the temperature trend chart comparing current observations against the 10-year normal.*

---

## 🔮 8. Future Scope

1. **Multi-lingual Support**: Hindi, Marathi, Tamil, Telugu, and Bengali voice & text interactions for rural farmers.
2. **Agricultural Crop Advisories**: Dynamic spray/harvest recommendations based on micro-climatic humidity and rain forecasts.
3. **IoT Micro-Station Integration**: Connecting localized low-cost IoT barometers and moisture sensors.
4. **Disaster Management Portal**: Automated webhook integration with NDRF / SDMA alert feeds.

---

**WeatherGPT • Smart India Hackathon 2026 Prototype**
