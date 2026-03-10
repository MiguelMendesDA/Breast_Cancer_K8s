import pandas as pd
from sqlalchemy import create_engine, text
import os

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

csv_file = "breast_cancer_df.csv"
df_csv = pd.read_csv(csv_file)

with engine.begin() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM training_data"))
    row_count = result.scalar()

if row_count == 0:
    print("Importing CSV into training_data...")
    df_csv.to_sql("training_data", con=engine, if_exists="append", index=False)
else:
    print(f"Table already has {row_count} rows. Skipping CSV import.")