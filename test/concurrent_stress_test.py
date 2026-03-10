import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost"
ENDPOINT = "/ml/predict"
URL = f"{BASE_URL}{ENDPOINT}"

TOTAL_REQUESTS = 1000
MAX_WORKERS = 200 


payload = {
    "gender": "Female",
    "smoking_habits": "No",
    "alcohol_habits": "Yes",
    "breastfeeding": "Yes",
    "oral_contraception": "No",
    "age": 42,
    "weight": 70,
    "height": 165,
    "bmi": 25.7
}


def send_request():
    start = time.time()
    response = requests.post(URL, json=payload)
    elapsed = time.time() - start
    return response.status_code, elapsed


def run_concurrent_test():
    print("\n================ CONCURRENT STRESS TEST ================\n")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Concurrent Workers: {MAX_WORKERS}\n")

    start_total = time.time()

    times = []
    failures = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(send_request) for _ in range(TOTAL_REQUESTS)]

        for future in as_completed(futures):
            status, elapsed = future.result()
            times.append(elapsed)

            if status != 200:
                failures += 1

    total_time = time.time() - start_total

    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)

    throughput = TOTAL_REQUESTS / total_time

    print("📊 RESULTS")
    print("--------------------------------------------------------")
    print(f"Total Execution Time: {total_time:.4f}s")
    print(f"Throughput: {throughput:.2f} requests/sec")
    print(f"Average Response Time: {avg_time:.4f}s")
    print(f"Min Response Time: {min_time:.4f}s")
    print(f"Max Response Time: {max_time:.4f}s")
    print(f"Failures: {failures}")
    print("--------------------------------------------------------\n")


if __name__ == "__main__":
    run_concurrent_test()