from fastapi import APIRouter, Query
from typing import Optional
from backend.models.schemas import ClimateInsightResponse, LocationSearchResult
from backend.services.climate_service import climate_service
from backend.services.weather_service import weather_service, DEFAULT_LOCATION

router = APIRouter(prefix="/api/climate", tags=["climate"])

@router.get("/insights", response_model=ClimateInsightResponse)
async def get_climate_insights(
    lat: float = Query(21.1458, description="Latitude"),
    lon: float = Query(79.0882, description="Longitude"),
    location: Optional[str] = Query(None, description="City name")
):
    loc_obj = None
    if location:
        results = await weather_service.search_location(location)
        if results:
            loc_obj = results[0]

    if not loc_obj:
        loc_obj = LocationSearchResult(
            name=location or "Nagpur",
            latitude=lat,
            longitude=lon,
            country="India",
            admin1="Maharashtra",
            country_code="IN",
            display_name=location or "Nagpur, Maharashtra, India"
        )

    return await climate_service.get_climate_insights(lat, lon, loc_obj)
