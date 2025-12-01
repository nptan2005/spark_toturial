import requests
from bs4 import BeautifulSoup

LOGIN_URL = "http://localhost:8082/login/"

s = requests.Session()
r = s.get(LOGIN_URL, timeout=10)
r.raise_for_status()

soup = BeautifulSoup(r.text, "html.parser")
csrf = soup.find("input", {"name": "csrf_token"})
token = csrf["value"] if csrf else None
print("CSRF token:", token)

payload = {
    "username": "admin",
    "password": "admin",
    "csrf_token": token
}
r2 = s.post(LOGIN_URL, data=payload, headers={"Referer": LOGIN_URL}, allow_redirects=True, timeout=10)
print("POST status:", r2.status_code)
print("Final URL:", r2.url)
print("Cookies:", s.cookies.get_dict())
print("If login succeeded you should see / or /home in final URL or HTML contains 'Logout' or user name.")