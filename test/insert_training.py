import requests

BASE_URL = "http://localhost"
ENDPOINT = "/ml/insert-training"

def test_insert_training():
    url = f"{BASE_URL}{ENDPOINT}"

    payload = {
        "gender": "Female",
        "smoking_habits": "No",
        "alcohol_habits": "Yes",
        "breastfeeding": "Yes",
        "oral_contraception": "No",
        "breast_cancer_history": "No",
        "age": 42,
        "weight": 70,
        "height": 165,
        "bmi": 25.7
    }

    print(f"📤 Sending request to {url} ...")

    response = requests.post(url, json=payload)

    print(f"\n📡 Status Code: {response.status_code}")

    try:
        print("📨 API Response:")
        print(response.json())
    except Exception:
        print("📨 Raw Response:")
        print(response.text)


if __name__ == "__main__":
    test_insert_training()