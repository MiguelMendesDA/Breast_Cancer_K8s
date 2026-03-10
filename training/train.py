import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib
import os
from datetime import datetime
import pickle

# --- MySQL configuration from env vars ---
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

# --- Paths ---
model_dir = "/app/models"
os.makedirs(model_dir, exist_ok=True)

# --- Load data from MySQL ---kubectl 
try:
    df = pd.read_sql("SELECT * FROM training_data", engine)
except Exception as e:
    print("Erro ao ler tabela training_data:", e)
    raise

# --- Prepare features and target ---
target_col = "breast_cancer_history"
X = df.drop(columns=[target_col, 'id'], errors='ignore')
y = df[target_col]

# --- Encode categorical features and save encoders ---
encoders = {}
for col in X.select_dtypes(include='object').columns:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col])
    encoders[col] = le

# Encode target
target_encoder = LabelEncoder()
y = target_encoder.fit_transform(y)

# --- Split train/test ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Train model ---
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# --- Evaluate ---
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model accuracy: {accuracy:.4f}")

# --- Determine new model version ---
with engine.begin() as conn:
    result = conn.execute(text("SELECT model_version FROM models ORDER BY id DESC LIMIT 1"))
    last_version = result.fetchone()
    if last_version:
        major, minor = map(int, last_version[0].split('.'))
        new_version = f"{major}.{minor + 1}"
    else:
        new_version = "1.0"

MODEL_VERSION = new_version
print(f"Training new model version: {MODEL_VERSION}")

# --- Save model and encoders to PVC ---
model_path = os.path.join(model_dir, f"breast_cancer_model_{MODEL_VERSION}.pkl")
joblib.dump(model, model_path)

encoders_path = os.path.join(model_dir, f"encoders_{MODEL_VERSION}.pkl")
with open(encoders_path, "wb") as f:
    pickle.dump({"features": encoders, "target": target_encoder}, f)

print(f"Model saved at: {model_path}")
print(f"Encoders saved at: {encoders_path}")

# --- Insert new version into models table ---
with engine.begin() as conn:
    conn.execute(
        text("INSERT INTO models (model_version, trained_at, accuracy) VALUES (:version, :trained_at, :accuracy)"),
        {"version": MODEL_VERSION, "trained_at": datetime.now(), "accuracy": accuracy}
    )
print(f"Model version {MODEL_VERSION} recorded in DB")
