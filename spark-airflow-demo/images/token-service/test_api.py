import requests

BASE_URL = "http://localhost:5000"

def test_generate_token(value):
    print(f"\n--- POST /token with value='{value}' ---")
    resp = requests.post(f"{BASE_URL}/token", json={"value": value})
    print("Status:", resp.status_code)
    print("Body:", resp.json())
    if resp.status_code == 200:
        return resp.json().get("token")
    return None

def test_get_token(token):
    print(f"\n--- GET /token/{token} ---")
    resp = requests.get(f"{BASE_URL}/token/{token}")
    print("Status:", resp.status_code)
    print("Body:", resp.json())

if __name__ == "__main__":
    # 1️⃣ Test generate token
    token = test_generate_token("hello-world")

    # 2️⃣ Test read token
    if token:
        test_get_token(token)

    # 3️⃣ Test invalid token
    test_get_token("TOKEN-99999")