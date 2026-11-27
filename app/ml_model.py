"""Load and use the trained soil-moisture prediction model."""
from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "soil_moisture_model.joblib"
FEATURES = ["soil_moisture", "temperature", "humidity", "light", "water_level"]


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Trained model is missing. Run: python scripts/train_model.py")
    return joblib.load(MODEL_PATH)


def predict_future_moisture(model, reading: dict) -> float:
    frame = pd.DataFrame([[float(reading[name]) for name in FEATURES]], columns=FEATURES)
    prediction = float(model.predict(frame)[0])
    return round(max(0.0, min(100.0, prediction)), 1)
