import os

from google.cloud import bigquery
import pandas as pd
import boto3
from datetime import datetime, timedelta


bq_client = bigquery.Client(project="retail-data-platfo")
s3_client = boto3.client('s3')

S3_BUCKET = "retail-data-platform-raw-yousef"


def extract_table(query, table_name, date):
    print(f"Extracting {table_name}...")
    
    df = bq_client.query(query).result().to_dataframe()
    
    file_name = f"{table_name}/{date}/{table_name}_{date}.csv"
    
    csv_buffer = df.to_csv(index=False)
    
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=file_name,
        Body=csv_buffer
    )
    
    print(f"Uploaded {len(df)} rows to s3://{S3_BUCKET}/{file_name}")
    return len(df)