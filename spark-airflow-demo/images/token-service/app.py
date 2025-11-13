from flask import Flask, request, jsonify
from prometheus_client import Histogram, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import time

app = Flask(__name__)

# histogram for response time
REQUEST_LATENCY = Histogram('token_service_response_seconds', 'Token service response time', buckets=(0.005,0.01,0.025,0.05,0.1,0.25,0.5,1,2,5))

store = {}

@app.route("/token", methods=["POST"])
def generate_token():
    start = time.time()
    data = request.json
    val = data.get("value")
    if not val:
        REQUEST_LATENCY.observe(time.time() - start)
        return jsonify({"error": "missing value"}), 400
    token = f"TOKEN-{len(store)+1}"
    store[token] = val
    REQUEST_LATENCY.observe(time.time() - start)
    return jsonify({"token": token})

@app.route("/token/<token>", methods=["GET"])
def get_token(token):
    start = time.time()
    val = store.get(token)
    REQUEST_LATENCY.observe(time.time() - start)
    if not val:
        return jsonify({"error": "token not found"}), 404
    return jsonify({"value": val})

# metrics endpoint for Prometheus
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route("/health")
def health():
    return jsonify(status="ok"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)