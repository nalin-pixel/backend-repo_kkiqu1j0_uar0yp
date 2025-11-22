import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Forecast, Alert, MeteogramRequest

app = FastAPI(title="Geo-temporal Weather Forecast Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InsertResponse(BaseModel):
    id: str


@app.get("/")
def root():
    return {"message": "Geo-temporal Weather Forecast Platform API"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ---------- Forecast Endpoints ----------
@app.post("/api/forecasts", response_model=InsertResponse)
async def create_forecast(forecast: Forecast):
    try:
        inserted_id = create_document("forecast", forecast)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecasts")
async def list_forecasts(model: Optional[str] = None, variable: Optional[str] = None, limit: int = Query(20, ge=1, le=200)):
    try:
        filt = {}
        if model:
            filt["model"] = model
        if variable:
            filt["variable"] = variable
        docs = get_documents("forecast", filt, limit)
        # convert ObjectId to string
        for d in docs:
            if d.get("_id"):
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecasts/{forecast_id}")
async def get_forecast(forecast_id: str):
    try:
        docs = get_documents("forecast", {"_id": ObjectId(forecast_id)}, 1)
        if not docs:
            raise HTTPException(status_code=404, detail="Forecast not found")
        d = docs[0]
        d["id"] = str(d.pop("_id"))
        return d
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Alerts Endpoints ----------
@app.post("/api/alerts", response_model=InsertResponse)
async def create_alert(alert: Alert):
    try:
        inserted_id = create_document("alert", alert)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts")
async def list_alerts(active: Optional[bool] = None, limit: int = Query(50, ge=1, le=500)):
    try:
        filt = {}
        if active is not None:
            filt["active"] = active
        docs = get_documents("alert", filt, limit)
        for d in docs:
            if d.get("_id"):
                d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Meteogram Endpoint (mock compute) ----------
@app.post("/api/meteogram")
async def generate_meteogram(req: MeteogramRequest):
    """
    For demo: synthesize a time series so the UI can render a meteogram.
    In a real system, we'd open NetCDF/xarray, subset by lat/lon, and return series.
    """
    import math
    import datetime as dt

    start = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    times = [ (start + dt.timedelta(hours=i)).isoformat() + "Z" for i in range(0, 49, 1) ]
    series = []
    for i, t in enumerate(times):
        base = 15 + 10 * math.sin(i/24*2*math.pi)
        noise = 1.5 * math.sin(i * 0.7)
        series.append(round(base + noise, 2))

    return {
        "lat": req.lat,
        "lon": req.lon,
        "variable": req.variable,
        "times": times,
        "values": series,
        "units": "°C" if req.variable == "t2m" else "units",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
