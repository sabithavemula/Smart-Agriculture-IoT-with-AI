"""Train and evaluate the demo future-soil-moisture regression model."""
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "synthetic_agriculture_readings.csv"
MODEL_DIR = ROOT / "models"
FEATURES = ["soil_moisture", "temperature", "humidity", "light", "water_level"]
TARGET = "future_soil_moisture_30min"


def metrics(model, x_test, y_test):
    pred = model.predict(x_test)
    return {
        "mae": round(float(mean_absolute_error(y_test, pred)), 3),
        "rmse": round(float(mean_squared_error(y_test, pred) ** 0.5), 3),
        "r2": round(float(r2_score(y_test, pred)), 4),
    }


def main():
    if not DATA.exists():
        raise SystemExit("Dataset missing. Run: python scripts/generate_dataset.py")
    df = pd.read_csv(DATA)
    x_train, x_test, y_train, y_test = train_test_split(
        df[FEATURES], df[TARGET], test_size=0.2, random_state=42
    )
    baseline = LinearRegression().fit(x_train, y_train)
    model = RandomForestRegressor(
        n_estimators=180, max_depth=12, min_samples_leaf=2,
        random_state=42, n_jobs=-1
    )
    model.fit(x_train, y_train)
    report = {
        "dataset_type": "synthetic demonstration data",
        "rows": int(len(df)),
        "features": FEATURES,
        "target": TARGET,
        "prediction_horizon": "30 minutes (simulated target)",
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "linear_regression_baseline": metrics(baseline, x_test, y_test),
        "random_forest_regression": metrics(model, x_test, y_test),
        "warning": "Metrics measure performance on synthetic data only; they do not establish real-world farm accuracy.",
    }
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_DIR / "soil_moisture_model.joblib")
    (MODEL_DIR / "training_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved trained model: {MODEL_DIR / 'soil_moisture_model.joblib'}")


if __name__ == "__main__":
    main()
