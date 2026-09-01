from fastapi import APIRouter, Query
from backend.models.schemas import LocationSearchResponse
from backend.services.weather_service import weather_service

router = APIRouter(prefix="/api/location", tags=["location"])

@router.get("/search", response_model=LocationSearchResponse)
async def search_locations(query: str = Query(..., min_length=1, description="City name or query")):
    results = await weather_service.search_location(query)
    return LocationSearchResponse(query=query, results=results)
