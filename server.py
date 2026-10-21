import json
import logging
from services.Optimization import Optimization
from services.DataSource import DataSource
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)

# Init flask server
app = Flask(__name__)
CORS(app)

# Data of the provider (NGSI-LD broker or data space connector)
data_source = DataSource()


@app.errorhandler(Exception)
def data_error(error):
    # Data space or broker failures (e.g. the consumer is not allowed yet)
    app.logger.exception("Request failed")
    return jsonify({"error": str(error)}), 502


# Serve frontend
@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


# API REST
@app.route("/wastecontainers")
def waste_containers():
    containers = data_source.waste_containers()
    return containers


@app.route("/trucks")
def trucks():
    trucks = get_trucks()
    return trucks


@app.route("/optimization")
def optimization():
    coords_raw = request.args.get("coords")
    vehicles_raw = request.args.get("vehicles")
    end_location_raw = request.args.get("end")
    if coords_raw is None or vehicles_raw is None or end_location_raw is None:
        return jsonify({
            "error": "Missing required parameters: coords, vehicles, end"
        }), 400
    coords = json.loads(coords_raw)
    vehicles = json.loads(vehicles_raw)
    end_location = json.loads(end_location_raw)
    optimizer = Optimization()
    optimization = optimizer.optimize(coords, vehicles, end_location)
    return optimization


# Data functions
def get_trucks():
    # Simulated trucks
    return [
        {
            "id": "urn:ngsi-ld:VehicleModel:vehiclemodelA:econic",
            "location": {
                "observedAt": "2023-11-16T23:01:12.111Z",
                "type": "GeoProperty",
                "value": {
                    "coordinates": [
                        -0.5236388090981838,
                        39.48451738852713 
                    ],
                    "type": "Point"
                }
            },
            "type": "VehicleModel",
            "brandName": "Mercedes Benz",
            "cargoVolume": 1000,
            "fuelType": "diesel",
            "manufacturerName": "Daimler",
            "modelName": "Econic",
            "name": "MBenz-Econic2014",
            "vehicleType": "lorry"
        }
    ]
