import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENWEATHER_API_KEY")

def is_valid(weather_data):
    if weather_data.get("name") is None:
        return False
    if weather_data.get("main", {}).get("temp") is None:
        return False
    return True

def get_weather(city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"   # trả về Celsius luôn, khỏi tự quy đổi từ Kelvin
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

data = get_weather("Hanoi")
if data and is_valid(data):
    # tiến hành insert vào Postgres
    pass
else:
    print("Dữ liệu thiếu trường bắt buộc, bỏ qua dòng này")

if __name__ == "__main__":
    data = get_weather("Hanoi")
    print(data)
