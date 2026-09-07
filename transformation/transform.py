import boto3
import pandas as pd
import numpy as np
from io import StringIO
from dotenv import load_dotenv
import os

load_dotenv()

s3_client = boto3.client('s3')

S3_BUCKET = "retail-data-platform-raw-yousef"
RAW_PREFIX = "historical"
TRANSFORMED_PREFIX = "transformed"

def read_from_s3(table_name):
    key = f"{table_name}/{RAW_PREFIX}/{table_name}_{RAW_PREFIX}.csv"
    
    response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
    
    content = response['Body'].read().decode('utf-8')
    
    df = pd.read_csv(StringIO(content))
    
    print(f"Read {len(df)} rows from {key}")
    
    return df

def write_to_s3(df, table_name):
    key = f"{table_name}/{TRANSFORMED_PREFIX}/{table_name}.csv"
    
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=csv_buffer.getvalue()
    )
    
    print(f"Written {len(df)} rows to {key}")






def build_dim_users(df_users):
    dim_users = df_users.rename(columns={"id": "user_id"})

    dim_users = dim_users[["user_id", "country", "city", "state", "latitude", "longitude"]]

    return dim_users


def build_dim_products(df_products):
    dim_products = df_products.rename(columns={"id": "product_id"})

    dim_products = dim_products[["product_id", "name", "category", "brand", "retail_price", "cost"]]

    return dim_products

def build_dim_distribution_centers(df_dc):
    dim_dc = df_dc.rename(columns={"id": "distribution_center_id"})
    dim_dc = dim_dc[["distribution_center_id", "name", "latitude", "longitude"]]
    return dim_dc

