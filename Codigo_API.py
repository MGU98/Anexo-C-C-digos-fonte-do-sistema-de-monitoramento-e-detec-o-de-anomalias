import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime

import uvicorn
from classifier import classify_sample, log_classification, get_all_logs, log_raw_window
import logging

# === Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anomaly_api")

# === FastAPI Init ===
app = FastAPI(title="Anomaly Detector API")

# === CORS para testes locais ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Modelo ===
class SensorData(BaseModel):
    x: List[float]
    y: List[float]
    z: List[float]
    current: List[float]

# === WebSocket Connections ===
connected_clients: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        # Enviar histórico completo ao conectar
        logs = get_all_logs()
        for row in logs:
            await websocket.send_text(json.dumps(row))

        while True:
            await websocket.receive_text()  # escuta mensagens (opcional)
    except:
        connected_clients.remove(websocket)


@app.get("/", response_class=PlainTextResponse)
async def check_ready():
    return "1"


# === POST Endpoint ===
@app.post("/")
async def predict_anomaly(payload: SensorData):
    try:
        # Converte dados em formato [[x, y, z, current], ...]
        data_matrix = list(zip(payload.x, payload.y, payload.z, payload.current))
        logger.info("Recebido %d amostras do sensor %s", len(data_matrix), "server")

        results = classify_sample(data_matrix)

        
        for result in results:
            result["sensor_id"] = "server"
            log_classification(result)

        log_raw_window("server", data_matrix)

        
        for result in results:
            data_json = json.dumps(result)
            for client in connected_clients:
                try:
                    await client.send_text(data_json)
                except:
                    connected_clients.remove(client)

        return results
    except Exception as e:
        logger.error("Erro na classificação: %s", str(e))
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4242)