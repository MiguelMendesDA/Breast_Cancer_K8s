import os
import asyncio
from datetime import datetime
import joblib
import pickle
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import create_engine, text, Table, MetaData

# -------------------------------
# MySQL configuration
# -------------------------------
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

if not all([MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB]):
    raise Exception("Missing required MySQL environment variables")

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

# -------------------------------
# Global variables for model
# -------------------------------
model = None
feature_encoders = None
target_encoder = None
MODEL_VERSION = None
MODEL_CHECK_INTERVAL = 60 

# -------------------------------
# Pydantic models
# -------------------------------
class PatientData(BaseModel):
    age: int
    gender: str
    smoking_habits: str
    alcohol_habits: str
    weight: float
    height: float
    bmi: float
    breastfeeding: str
    oral_contraception: str

class TrainingData(PatientData):
    breast_cancer_history: str 

# -------------------------------
# Validation functions
# -------------------------------
def validate_yes_no(field_name, value):
    allowed = ["Yes", "No"]
    v_clean = str(value).strip().capitalize()
    if v_clean not in allowed:
        raise ValueError(f"Invalid value for '{field_name}': '{value}'. Allowed: {allowed}")
    return v_clean

def validate_gender(value):
    allowed = ["Male", "Female"]
    v_clean = str(value).strip().capitalize()
    if v_clean not in allowed:
        raise ValueError(f"Invalid value for 'gender': '{value}'. Allowed: {allowed}")
    return v_clean

def validate_numeric(field_name, value, min_val, max_val):
    if not (min_val <= value <= max_val):
        raise ValueError(f"Invalid value for '{field_name}': {value}. Must be between {min_val} and {max_val}")
    return value

def validate_and_normalize_patient(data: dict, include_history=False):
    data = data.copy()

    data["gender"] = validate_gender(data["gender"])
    data["smoking_habits"] = validate_yes_no("smoking_habits", data["smoking_habits"])
    data["alcohol_habits"] = validate_yes_no("alcohol_habits", data["alcohol_habits"])
    data["breastfeeding"] = validate_yes_no("breastfeeding", data["breastfeeding"])
    data["oral_contraception"] = validate_yes_no("oral_contraception", data["oral_contraception"])

    data["age"] = validate_numeric("age", data["age"], 1, 119)
    data["weight"] = validate_numeric("weight", data["weight"], 1, 500)
    data["height"] = validate_numeric("height", data["height"], 1, 250)
    data["bmi"] = validate_numeric("bmi", data["bmi"], 1, 100)

    if include_history:
        data["breast_cancer_history"] = validate_yes_no(
            "breast_cancer_history",
            data["breast_cancer_history"]
        )

    return data

# -------------------------------
# Model loading
# -------------------------------
def load_model(version):
    global model, feature_encoders, target_encoder, MODEL_VERSION

    model_path = f"/app/models/breast_cancer_model_{version}.pkl"
    encoders_path = f"/app/models/encoders_{version}.pkl"

    if not os.path.exists(model_path) or not os.path.exists(encoders_path):
        raise Exception(f"Model or encoders for version {version} not found.")

    model = joblib.load(model_path)

    with open(encoders_path, "rb") as f:
        encoders_data = pickle.load(f)

    feature_encoders = encoders_data["features"]
    target_encoder = encoders_data["target"]
    MODEL_VERSION = version

    print(f"Loaded model version {MODEL_VERSION}")

async def model_watcher():
    global MODEL_VERSION

    while True:
        await asyncio.sleep(MODEL_CHECK_INTERVAL)

        with engine.begin() as conn:
            result = conn.execute(
                text("SELECT model_version FROM models ORDER BY id DESC LIMIT 1")
            )
            last_version = result.scalar()

        if last_version and last_version != MODEL_VERSION:
            print(f"New model version detected: {last_version}, reloading...")
            load_model(last_version)

# -------------------------------
# FastAPI initialization
# -------------------------------
app = FastAPI(title="Breast Cancer Prediction API")

@app.on_event("startup")
async def startup_event():
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT model_version FROM models ORDER BY id DESC LIMIT 1")
        )
        last_version = result.scalar()

    if not last_version:
        raise Exception("No trained model found in DB")

    load_model(last_version)

    asyncio.create_task(model_watcher())

# -------------------------------
# Auxiliary insertion function
# -------------------------------
def insert_training_row(data_dict: dict):
    metadata = MetaData()
    training_table = Table("training_data", metadata, autoload_with=engine)

    with engine.begin() as conn:
        conn.execute(training_table.insert(), [data_dict])
    return 1

# -------------------------------
# Prediction endpoint
# -------------------------------
@app.post("/predict")
def predict(data: PatientData):
    try:
        data_dict = validate_and_normalize_patient(data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    df = pd.DataFrame([data_dict])

    for col, le in feature_encoders.items():
        if col in df.columns:
            df[col] = le.transform(df[col])

    pred_encoded = model.predict(df)[0]
    pred_label = target_encoder.inverse_transform([pred_encoded])[0]

    row = df.iloc[0].to_dict()
    row.update({
        "prediction": pred_label,
        "model_version": MODEL_VERSION,
        "created_at": datetime.now()
    })

    metadata = MetaData()
    predictions_table = Table("predictions", metadata, autoload_with=engine)

    with engine.begin() as conn:
        conn.execute(predictions_table.insert(), [row])

    return {"Breast Cancer Risk Prediction": pred_label}

# -------------------------------
# Insert single training row
# -------------------------------
@app.post("/insert-training")
def insert_training(data: TrainingData):
    try:
        data_dict = validate_and_normalize_patient(data.dict(), include_history=True)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    inserted_rows = insert_training_row(data_dict)
    return {"status": "success", "inserted_rows": inserted_rows}

# -------------------------------
# Upload CSV endpoint
# -------------------------------
@app.post("/upload-training-csv")
async def upload_training_csv(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler CSV: {e}")

    required_columns = [
        "age", "gender", "smoking_habits", "alcohol_habits",
        "weight", "height", "bmi", "breastfeeding",
        "oral_contraception", "breast_cancer_history"
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {missing_columns}"
        )
  
    df_clean = df.dropna(subset=required_columns)

    inserted_count = 0
    errors = []

    for idx, row in df_clean.iterrows():
        try:
            data_dict = validate_and_normalize_patient(row.to_dict(), include_history=True)
            insert_training_row(data_dict)
            inserted_count += 1
        except ValueError as e:
            errors.append({"row": idx, "error": str(e)})

    return {"status": "completed", "inserted_rows": inserted_count, "errors": errors}