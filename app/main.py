from datetime import datetime, timezone
from pathlib import Path
import random
import sqlite3
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .ml_model import load_model, predict_future_moisture

ROOT = Path(__file__).resolve().parent.parent
BASE = Path(__file__).resolve().parent
DB_PATH = ROOT / "agriculture.db"
app = FastAPI(title="Smart Agriculture Using IoT with AI Prediction", version="2.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
state_lock = Lock()
auto_irrigation = True
pump_on = False
latest_decision = "wait"
ml_model = None


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'simulator',
            soil_moisture REAL NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            light REAL NOT NULL,
            water_level REAL NOT NULL,
            predicted_moisture REAL,
            recommendation TEXT
        )""")


init_db()


class ReadingInput(BaseModel):
    soil_moisture: float = Field(ge=0, le=100)
    temperature: float = Field(ge=-20, le=70)
    humidity: float = Field(ge=0, le=100)
    light: float = Field(ge=0, le=100)
    water_level: float = Field(ge=0, le=100)


def latest_reading():
    with connect() as db:
        row = db.execute("SELECT * FROM readings ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def decide_irrigation(current: float, predicted: float, water: float) -> str:
    if water <= 5:
        return "water_low"
    return "irrigate" if current < 30 or predicted < 30 else "wait"


def store_reading(item: ReadingInput, source: str):
    global pump_on, latest_decision
    values = item.model_dump()
    prediction = predict_future_moisture(ml_model, values)
    decision = decide_irrigation(values["soil_moisture"], prediction, values["water_level"])
    stamp = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cur = db.execute("""INSERT INTO readings
            (timestamp, source, soil_moisture, temperature, humidity, light, water_level, predicted_moisture, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (stamp, source, values["soil_moisture"], values["temperature"], values["humidity"],
             values["light"], values["water_level"], prediction, decision))
        row = db.execute("SELECT * FROM readings WHERE id=?", (cur.lastrowid,)).fetchone()
    with state_lock:
        latest_decision = decision
        pump_on = auto_irrigation and decision == "irrigate"
    return dict(row)


@app.on_event("startup")
def startup():
    global ml_model
    try:
        ml_model = load_model()
    except FileNotFoundError as exc:
        raise RuntimeError(str(exc)) from exc


@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": ml_model is not None, "hardware": "not connected; simulator mode"}


@app.get("/api/readings")
def readings(limit: int = 40):
    with connect() as db:
        rows = db.execute("SELECT * FROM readings ORDER BY id DESC LIMIT ?", (max(1, min(limit, 200)),)).fetchall()
    return [dict(row) for row in reversed(rows)]


@app.post("/api/esp32/readings")
def receive_esp32_reading(item: ReadingInput):
    """Endpoint intended for ESP32 Wi-Fi POST requests; simulator can call it too."""
    return store_reading(item, "esp32_or_simulator")


@app.post("/api/demo-reading")
def demo_reading():
    """Generate one simulated sensor packet for a no-hardware demonstration."""
    previous = latest_reading() or {"soil_moisture": 48, "temperature": 28, "humidity": 65, "light": 60, "water_level": 80}
    moisture = max(10, min(85, previous["soil_moisture"] + random.uniform(-3.5, 1.2)))
    item = ReadingInput(
        soil_moisture=round(moisture, 1),
        temperature=round(random.uniform(24, 36), 1),
        humidity=round(random.uniform(42, 82), 1),
        light=round(random.uniform(30, 95), 1),
        water_level=round(max(5, min(100, previous["water_level"] - random.uniform(0, 0.8))), 1),
    )
    return store_reading(item, "simulator")


@app.get("/api/prediction")
def prediction():
    row = latest_reading()
    if not row:
        return {"message": "Waiting for first sensor reading"}
    return {
        "model": "RandomForestRegressor",
        "prediction_horizon": "30 minutes (synthetic demonstration model)",
        "predicted_moisture": row["predicted_moisture"],
        "recommendation": row["recommendation"],
    }


@app.get("/api/status")
def status():
    row = latest_reading()
    with state_lock:
        return {
            "mode": "automatic" if auto_irrigation else "disabled",
            "pump_on": pump_on,
            "recommendation": latest_decision,
            "water_level": "low" if row and row["water_level"] <= 5 else "ok",
            "pump_control": "software simulation only",
        }


@app.post("/api/mode")
def set_mode(enabled: bool):
    global auto_irrigation, pump_on
    with state_lock:
        auto_irrigation = enabled
        if not enabled:
            pump_on = False
    return status()


@app.get("/api/model-info")
def model_info():
    metrics_path = ROOT / "models" / "training_metrics.json"
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Training report not found")
    import json
    return json.loads(metrics_path.read_text(encoding="utf-8"))
