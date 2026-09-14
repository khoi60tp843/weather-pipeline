import requests
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from datetime import datetime
from urllib.parse import quote_plus 

load_dotenv()
api_key = os.getenv("OPENWEATHER_API_KEY")
db_password = quote_plus(os.getenv("DB_PASSWORD"))   # encode here

CITIES = ["Hanoi", "Ho Chi Minh City", "Da Nang"]

def get_weather(city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}

    try:
        response = requests.get(url, params=params, timeout=(3, 10))
    except requests.exceptions.RequestException as e:
        print(f"Network error for {city}: {e}")
        return None

    if response.status_code == 200:
        return response.json()
    print(f"Error {response.status_code} for {city}: {response.text}")
    return None

def is_valid(data):
    if data is None:
        return False
    if data.get("name") is None:
        return False
    if data.get("main", {}).get("temp") is None:
        return False
    return True

def extract_fields(data, queried_city):
    return {
        "city": queried_city,   # dùng tên mình đã query, không dùng data["name"]
        "temperature_c": data["main"]["temp"],
        "humidity": data["main"].get("humidity"),
        "description": data["weather"][0]["description"] if data.get("weather") else None,
        "recorded_at": datetime.now()
    }

def collect_weather_data(cities):
    rows = []
    for city in cities:
        raw = get_weather(city)
        if is_valid(raw):
            rows.append(extract_fields(raw, city))   # truyền thêm city gốc vào
        else:
            print(f"Skipping {city}: invalid or missing data")
    return rows

def save_to_postgres(rows):
    if not rows:
        print("No valid rows to save.")
        return
    df = pd.DataFrame(rows)
    engine = create_engine(f"postgresql://postgres:{db_password}@localhost:5432/weather_db")
    df.to_sql("weather_readings", engine, if_exists="append", index=False)
    print(f"Inserted {len(df)} rows into weather_readings.")

if __name__ == "__main__":
    rows = collect_weather_data(CITIES)
    save_to_postgres(rows)
