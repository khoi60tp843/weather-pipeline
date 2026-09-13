# Weather Data Pipeline

A small end-to-end data engineering project that automatically collects weather data from a public API, stores it in a relational database, and serves it through a REST API.

## Overview

This pipeline runs on a schedule, fetches current weather conditions for a set of cities, cleans and transforms the raw response, persists it to PostgreSQL, and exposes the accumulated historical data through a FastAPI endpoint. The goal is to build the kind of time-series dataset that a free-tier weather API does not provide on its own (OpenWeatherMap's free tier only exposes the *current* conditions, not history).

## Architecture

```
Windows Task Scheduler (every 15 min)
        │
        ▼
OpenWeatherMap API  ──fetch raw JSON──▶  Pandas  ──clean & transform──▶  PostgreSQL
                                                                              │
                                                                              ▼
                                                                    FastAPI (GET /weather)
```

| Stage | Tool | Responsibility |
|---|---|---|
| Trigger | Windows Task Scheduler | Runs the collection script every 15 minutes |
| Source | OpenWeatherMap API | Provides current weather conditions per city |
| Transform | Pandas | Cleans and structures raw JSON into tabular form |
| Storage | PostgreSQL | Persists readings over time |
| Serving | FastAPI | Exposes stored data via a REST endpoint |

## Tech Stack

- **Python 3.13**
- `requests` — HTTP calls to the weather API
- `pandas` — data cleaning and transformation
- `SQLAlchemy` + `psycopg2-binary` — database connection and inserts
- `PostgreSQL` — storage
- `FastAPI` + `uvicorn` — REST API layer
- `python-dotenv` — secrets management
- Windows Task Scheduler — automation

## Project Structure

```
weather_pipeline/
├── fetch_weather.py     # calls the OpenWeatherMap API
├── save_weather.py      # fetch -> validate -> transform -> insert into Postgres
├── main.py               # FastAPI app serving stored readings
├── .env                  # API key + DB password (not committed)
├── .gitignore
└── README.md
```

## Setup

1. Clone the repository and install dependencies:
   ```bash
   pip install requests pandas sqlalchemy psycopg2-binary python-dotenv fastapi uvicorn
   ```

2. Create a PostgreSQL database named `weather_db`, then run:
   ```sql
   CREATE TABLE weather_readings (
       id SERIAL PRIMARY KEY,
       city VARCHAR(100) NOT NULL,
       temperature_c REAL NOT NULL,
       humidity INTEGER,
       description VARCHAR(200),
       recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
   );
   ```

3. Create a `.env` file in the project root:
   ```
   OPENWEATHER_API_KEY=your_key_here
   DB_PASSWORD=your_postgres_password
   ```

4. Run the collector once to test:
   ```bash
   python save_weather.py
   ```

5. Start the API:
   ```bash
   uvicorn main:app --reload
   ```
   Then visit `http://127.0.0.1:8000/docs` for interactive API docs.

6. (Optional) Automate collection via Windows Task Scheduler to run `save_weather.py` on a recurring interval.

## API

`GET /weather`

| Query param | Type | Description |
|---|---|---|
| `city` | string, optional | Filter results by city name |
| `limit` | int, optional (default 50) | Max number of rows returned, most recent first |

## Design Decisions

A few choices worth calling out, since they're the parts that actually took thought:

- **Parameterized SQL queries, not string formatting.** The FastAPI endpoint builds queries with SQLAlchemy's `:param` placeholders instead of f-string interpolation, to avoid SQL injection.
- **`if_exists="append"`, not `"replace"`, on insert.** The whole point of the pipeline is to accumulate history over time — replacing the table on every run would defeat that.
- **The city name is taken from the input query, not from the API's response.** OpenWeatherMap's internal geocoding database returned `"Turan"` for a query of `"Da Nang"` — an old French colonial-era name (Tourane) still stored as the canonical name for that location. Relying on a third-party API's own naming for an identifier you don't control is fragile, so the pipeline stores the city name it was queried with instead, keeping it consistent with how the data is later filtered.
- **Secrets are read from environment variables via `.env`**, which is excluded from version control, rather than hardcoded — standard practice for anything that grants access to an external service or database.
- **Invalid or incomplete API responses are skipped, not allowed to crash the run.** A single malformed response (missing fields, city not found) is logged and skipped so the rest of the batch still completes.

## Possible Next Steps

- Add a lightweight chart (e.g. `matplotlib`) to visualize temperature trends over time
- Add automated tests for the data validation logic
- Move the schema definition into a versioned `schema.sql` / migration file
