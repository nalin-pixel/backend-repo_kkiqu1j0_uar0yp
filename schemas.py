"""
Database Schemas for Geo-temporal Weather Forecast Platform

Collections are derived from class names in lowercase.
- Forecast -> "forecast"
- Alert -> "alert"

We store forecast metadata and lightweight data products to power
meteograms, map overlays, and historical comparisons.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ForecastGridPoint(BaseModel):
    lat: float
    lon: float
    values: List[float] = Field(..., description="Time-ordered scalar values (e.g., temperature)")


class Forecast(BaseModel):
    model: Literal["WRF", "GFS", "ICON", "ECMWF"] = "WRF"
    init_time: str = Field(..., description="ISO timestamp for model initialization")
    lead_hours: int = Field(..., ge=1, le=240)
    variable: Literal["t2m", "u10", "v10", "precip", "mslp"] = "t2m"
    bbox: List[float] = Field(..., min_items=4, max_items=4, description="[minLon, minLat, maxLon, maxLat]")
    grid_res_km: float = 10.0
    times: List[str] = Field(..., description="ISO timestamps for each forecast step")
    grid: List[ForecastGridPoint] = Field(..., description="Flat list of grid points with time-series values")


class Alert(BaseModel):
    name: str
    variable: Literal["t2m", "precip", "mslp"] = "t2m"
    threshold: float
    comparison: Literal[">=", ">", "<=", "<"] = ">="
    polygon: List[List[float]] = Field(..., description="Array of [lon, lat] making a closed ring")
    active: bool = True


class MeteogramRequest(BaseModel):
    lat: float
    lon: float
    variable: Literal["t2m", "precip", "mslp"] = "t2m"
    forecast_id: Optional[str] = None
