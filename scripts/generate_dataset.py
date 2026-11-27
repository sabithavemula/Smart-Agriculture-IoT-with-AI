"""Create a reproducible synthetic dataset for the software demonstration.

The target is a simulated soil-moisture value 30 minutes after each row.
This is synthetic teaching/demo data, not measured farm data.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "synthetic_agriculture_readings.csv"


def main():
    rng = np.random.default_rng(42)
    n = 5000
    moisture = rng.uniform(18, 85, n)
    temperature = rng.uniform(18, 42, n)
    humidity = rng.uniform(25, 95, n)
    light = rng.uniform(5, 100, n)
    water = rng.uniform(0, 100, n)

    # Transparent synthetic scenario: heat/light increase drying; humidity
    # moderates it; available water and starting moisture affect future moisture.
    drying = (temperature - 18) * 0.12 + light * 0.025 - (humidity - 25) * 0.018
    future = moisture - drying + (water / 100) * 0.9 + rng.normal(0, 1.4, n)
    future = np.clip(future, 0, 100)
    frame = pd.DataFrame({
        "soil_moisture": moisture,
        "temperature": temperature,
        "humidity": humidity,
        "light": light,
        "water_level": water,
        "future_soil_moisture_30min": future,
    }).round(2)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=False)
    print(f"Created {len(frame)} synthetic rows: {OUT}")
    print("Reminder: these are simulated values, not real farm measurements.")


if __name__ == "__main__":
    main()
