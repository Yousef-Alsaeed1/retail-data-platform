import os

from google.cloud import bigquery
import pandas as pd
import boto3
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()


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

def run_extraction(mode="incremental"):
    if mode == "historical":
        date_filter = "DATE(created_at) < CURRENT_DATE()"
        date = "historical"
    else:
        yesterday = datetime.now() - timedelta(days=1)
        date = yesterday.strftime("%Y-%m-%d")
        date_filter = f"DATE(created_at) = '{date}'"
    
    print(f"Running {mode} extraction for {date}")

    queries = {
        "orders": f"""
            SELECT 
                order_id,
                user_id,
                status,
                created_at,
                shipped_at,
                delivered_at,
                num_of_item
            FROM `bigquery-public-data.thelook_ecommerce.orders`
            WHERE {date_filter}
        """,
        
        "order_items": f"""
            SELECT
                id,
                order_id,
                user_id,
                product_id,
                status,
                created_at,
                shipped_at,
                delivered_at,
                returned_at,
                sale_price
            FROM `bigquery-public-data.thelook_ecommerce.order_items`
            WHERE {date_filter}
        """,
        
        "users": f"""
            SELECT
                id,
                first_name,
                last_name,
                email,
                country,
                city,
                state,
                latitude,
                longitude
            FROM `bigquery-public-data.thelook_ecommerce.users`
            WHERE {date_filter}
        """,
        
        "products": f"""
            SELECT
                id,
                name,
                category,
                brand,
                retail_price,
                cost,
                distribution_center_id
            FROM `bigquery-public-data.thelook_ecommerce.products`
        """,
        
        "distribution_centers": f"""
            SELECT
                id,
                name,
                latitude,
                longitude
            FROM `bigquery-public-data.thelook_ecommerce.distribution_centers`
        """
    }
    total_rows = 0
    for table_name, query in queries.items():
        rows = extract_table(query, table_name, date)
        total_rows += rows
    
    print(f"Extraction complete. Total rows extracted: {total_rows}")

if __name__ == "__main__":
    run_extraction(mode="historical")