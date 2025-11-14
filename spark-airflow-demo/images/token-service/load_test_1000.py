import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:5000/token"
THREADS = 1000

def send_request(i):
    resp = requests.post(BASE_URL, json={"value": f"val-{i}"})
    return resp.status_code, resp.text

def main():
    results = []
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = [executor.submit(send_request, i) for i in range(THREADS)]

        for f in as_completed(futures):
            try:
                results.append(f.result())
            except Exception as e:
                results.append(("ERROR", str(e)))

    print("\nDONE. Summary:")
    print(f"Total requests: {len(results)}")
    print("Sample 10 results:")
    for r in results[:10]:
        print(r)

if __name__ == "__main__":
    main()