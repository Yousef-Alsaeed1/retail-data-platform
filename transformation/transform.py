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


def build_fact_table(df_order_items, df_products, df_orders):

    order_dates = df_orders[["order_id", "created_at"]].rename(
        columns={"created_at": "order_created_at"}
    )
    product_centers = df_products[["id", "distribution_center_id"]].rename(
        columns={"id": "product_id"}
    )   

    fact_orders = df_order_items.merge(
        product_centers,
        on="product_id",
        how="left",
        validate="many_to_one"
    )    

    fact_orders = fact_orders.merge(
        order_dates,
        on="order_id",
        how="left",
        validate="many_to_one"
    )

    fact_orders = fact_orders.rename(columns={"id": "order_item_id"})


    timestamp_columns = [
        "created_at",
        "order_created_at",
        "shipped_at",
        "delivered_at",
        "returned_at"
    ]

    for column in timestamp_columns:
        fact_orders[column] = pd.to_datetime(
            fact_orders[column],
            format="ISO8601",
            utc=True
        )



    fact_orders["prep_time"] = fact_orders["shipped_at"] - fact_orders["order_created_at"]
    fact_orders["delivery_time"] = fact_orders["delivered_at"] - fact_orders["shipped_at"]



    fact_orders["delivery_time"] = fact_orders["delivery_time"].dt.total_seconds() / 3600
    fact_orders["prep_time"] = fact_orders["prep_time"].dt.total_seconds() / 3600


    slow_threshold = fact_orders["delivery_time"].quantile(0.75)

    #we make it boolean not bool so we can use null values in the column
    fact_orders["is_slow"] = slow_threshold < fact_orders["delivery_time"]
    fact_orders["is_slow"] = fact_orders["is_slow"].astype("boolean") 

# making the is_slow column null for the rows where delivery_time is null
    missing_delivery = fact_orders["delivery_time"].isna()
    fact_orders.loc[missing_delivery, "is_slow"] = pd.NA


    fact_orders = fact_orders[[
        "order_item_id", "order_id", "product_id", "distribution_center_id","user_id", "sale_price", "status",
        "created_at", "order_created_at", "shipped_at", "delivered_at", "returned_at",
        "prep_time", "delivery_time", "is_slow"
    ]]

    return fact_orders


def run_transformation():
    print("Starting transformation...")

    users_df = read_from_s3("users")
    dim_users_df = build_dim_users(users_df)
    write_to_s3(dim_users_df, "dim_users")

    products_df = read_from_s3("products")
    dim_products_df = build_dim_products(products_df)
    write_to_s3(dim_products_df, "dim_products")

    distribution_centers_df = read_from_s3("distribution_centers")      
    dim_distribution_centers_df = build_dim_distribution_centers(distribution_centers_df)
    write_to_s3(dim_distribution_centers_df, "dim_distribution_centers")


    orders_df = read_from_s3("orders")
    order_items_df = read_from_s3("order_items")
    fact_orders_df = build_fact_table(order_items_df, products_df, orders_df)  
    write_to_s3(fact_orders_df, "fact_orders")

    print("Fact rows:", len(fact_orders_df))
    print("Negative preparation times:", (fact_orders_df["prep_time"] < 0).sum())
    print("Negative delivery times:", (fact_orders_df["delivery_time"] < 0).sum())
    print(
    "Missing parent creation timestamps:",
    fact_orders_df["order_created_at"].isna().sum()
    )
    print("finished transformation")



if __name__ == "__main__":
    run_transformation()
