import os
import time
import hmac
import hashlib
from flask import Flask, request, jsonify
from prometheus_client import Histogram, generate_latest, CONTENT_TYPE_LATEST
from logging.handlers import RotatingFileHandler
import logging

app = Flask(__name__)

# -------------------------
# Logging config
# -------------------------
LOG_FOLDER = "/app/logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

handler = RotatingFileHandler(
    f"{LOG_FOLDER}/app.log", 
    maxBytes=5 * 1024 * 1024, 
    backupCount=5
)
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s %(module)s:%(lineno)d - %(message)s'
)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# -------------------------
# Prometheus metrics
# -------------------------
REQUEST_LATENCY = Histogram(
    'token_service_response_seconds',
    'Token service response time',
    buckets=(0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2,5)
)

# -------------------------
# HMAC secret key
# -------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "DEFAULT_SECRET_KEY_CHANGE_ME")

store = {}  # demo store

# -------------------------
# Function: generate hashed token
# -------------------------
def generate_hash(value: str) -> str:
    """
    Create HMAC-SHA256 hash, same input -> same hash.
    Cannot reverse.
    """
    hashed = hmac.new(
        SECRET_KEY.encode(),
        value.encode(),
        hashlib.sha256
    ).hexdigest()
    return hashed


@app.route("/token", methods=["POST"])
def create_token():
    start = time.time()
    data = request.json

    if not data or "value" not in data:
        REQUEST_LATENCY.observe(time.time() - start)
        app.logger.warning("Missing value in request")
        return jsonify({"error": "missing value"}), 400

    value = data["value"]
    token = generate_hash(value)
    store[token] = value

    app.logger.info(f"Generated token for value='{value}' token='{token}'")

    REQUEST_LATENCY.observe(time.time() - start)
    return jsonify({"token": token})


@app.route("/token/<token>", methods=["GET"])
def get_value(token):
    start = time.time()
    value = store.get(token)

    if not value:
        REQUEST_LATENCY.observe(time.time() - start)
        app.logger.warning(f"Token not found: {token}")
        return jsonify({"error": "token not found"}), 404

    REQUEST_LATENCY.observe(time.time() - start)
    return jsonify({"value": value})


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    app.logger.info("Token service starting...")
    app.run(host="0.0.0.0", port=5000)