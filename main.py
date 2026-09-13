from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_password = os.getenv("DB_PASSWORD")

app = FastAPI()
engine = create_engine(f"postgresql://postgres:{db_password}@localhost:5432/weather_db")

@app.get("/weather")
def get_weather(city: str = Query(None), limit: int = 50):
    query = "SELECT * FROM weather_readings"
    params = {}

    if city:
        query += " WHERE city = :city"
        params["city"] = city

    query += " ORDER BY recorded_at DESC LIMIT :limit"
    params["limit"] = limit

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = [dict(row._mapping) for row in result]

    return rows