import json
import numpy as np
import joblib
from datetime import datetime
import csv
from pathlib import Path

model = joblib.load("oneclass_svm_model.pkl")
scaler = joblib.load("scaler.pkl")


def classify_sample(sample):
    data = np.array(sample) 

    
    scaled = scaler.transform(data) 

    predictions = model.predict(scaled)  
    distances = model.decision_function(scaled) 
    confidences = [max(0.0, min(1.0, 1 - np.tanh(abs(d)))) for d in distances]

    results = []
    for i in range(len(data)):
        results.append({
            "timestamp": datetime.now().isoformat(),
            "x": float(data[i][0]),
            "y": float(data[i][1]),
            "z": float(data[i][2]),
            "current": float(data[i][3]),
            "is_anomaly": bool(predictions[i] == -1),
            "distance": float(distances[i]),
            "confidence": float(confidences[i])
        })

    return results


def log_classification(data: dict):
    CSV_FILE = Path("logs/classifications.csv")
    CSV_FILE.parent.mkdir(exist_ok=True)
    write_header = not CSV_FILE.exists()

    log_row = {
        "timestamp": data["timestamp"],
        "sensor_id": data["sensor_id"],
        "is_anomaly": data["is_anomaly"],
        "distance": data["distance"],
        "confidence": data["confidence"],
        "x": data["x"],
        "y": data["y"],
        "z": data["z"],
        "current": data["current"]
    }

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=log_row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(log_row)

def log_raw_window(sensor_id: str, sample: list):
    CSV_FILE = Path("logs/raw_samples.csv")
    CSV_FILE.parent.mkdir(exist_ok=True)
    write_header = not CSV_FILE.exists()

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "sensor_id", "x", "y", "z", "current"])
        if write_header:
            writer.writeheader()

        for x, y, z, current in sample:
            writer.writerow({
                "timestamp": datetime.now().isoformat(),
                "sensor_id": sensor_id,
                "x": x,
                "y": y,
                "z": z,
                "current": current
            })

def get_all_logs():
    CSV_FILE = Path("logs/classifications.csv")
    if not CSV_FILE.exists():
        return []

    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]