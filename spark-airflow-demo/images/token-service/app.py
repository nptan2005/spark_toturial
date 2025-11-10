from flask import Flask, request, jsonify

app = Flask(__name__)

# Simple token store
store = {}

@app.route("/token", methods=["POST"])
def generate_token():
    data = request.json
    val = data.get("value")
    if not val:
        return jsonify({"error": "missing value"}), 400
    token = f"TOKEN-{len(store)+1}"
    store[token] = val
    return jsonify({"token": token})

@app.route("/token/<token>", methods=["GET"])
def get_token(token):
    val = store.get(token)
    if not val:
        return jsonify({"error": "token not found"}), 404
    return jsonify({"value": val})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)