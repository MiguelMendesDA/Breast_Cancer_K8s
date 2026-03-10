import requests
import sys
from pathlib import Path

BASE_URL = "http://localhost" 
ENDPOINT = "/ml/upload-training-csv"


def upload_csv(file_path: str):
    url = f"{BASE_URL}{ENDPOINT}"
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "text/csv")}
        print(f"📤 Uploading {file_path.name} to {url} ...")
        response = requests.post(url, files=files)

    print(f"\n📡 Status Code: {response.status_code}")

    try:
        print("📨 API Response:")
        print(response.json())
    except Exception:
        print("📨 Raw Response:")
        print(response.text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_csv.py path/to/file.csv")
        sys.exit(1)

    upload_csv(sys.argv[1])