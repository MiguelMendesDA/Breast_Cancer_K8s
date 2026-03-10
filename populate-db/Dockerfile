FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY populate-db.py .
COPY ../data/breast_cancer_df.csv .

CMD ["python", "populate-db.py"]