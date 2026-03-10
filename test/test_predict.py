import requests

BASE_URL = "http://localhost"
ENDPOINT = "/ml/predict"
URL = f"{BASE_URL}{ENDPOINT}"


def send_request(name, payload):
    print("\n" + "="*60)
    print(f"🧪 TEST CASE: {name}")
    print("="*60)
    print("📤 Payload:")
    print(payload)

    response = requests.post(URL, json=payload)
    print(f"\n📡 Status Code: {response.status_code}")

    try:
        print("🧠 Prediction Response:")
        print(response.json())
    except Exception:
        print("📨 Raw Response:")
        print(response.text)


def run_tests():
    # ✅ Valid case 1
    payload1 = {
        "gender": "Female",
        "smoking_habits": "Yes",
        "alcohol_habits": "Yes",
        "breastfeeding": "Yes",
        "oral_contraception": "No",
        "age": 62,
        "weight": 80,
        "height": 165,
        "bmi": 29.4
    }

    # ✅ Valid case 2
    payload2 = {
        "gender": "Male",
        "smoking_habits": "No",
        "alcohol_habits": "No",
        "breastfeeding": "No",
        "oral_contraception": "No",
        "age": 55,
        "weight": 75,
        "height": 170,
        "bmi": 26.0
    }

    # ❌ Invalid gender
    payload3 = {
        **payload1,
        "gender": "Unknown"
    }

    # ❌ Invalid Yes/No field
    payload4 = {
        **payload1,
        "smoking_habits": "Sometimes"
    }

    # ❌ BMI out of range
    payload5 = {
        **payload1,
        "bmi": 150
    }

    # ❌ Missing required field
    payload6 = payload1.copy()
    del payload6["height"]

    tests = [
        ("Valid Case 1", payload1),
        ("Valid Case 2", payload2),
        ("Invalid Gender", payload3),
        ("Invalid Smoking Field", payload4),
        ("Invalid BMI", payload5),
        ("Missing Height Field", payload6),
    ]

    for name, payload in tests:
        send_request(name, payload)


if __name__ == "__main__":
    run_tests()