from google.cloud import bigquery

client = bigquery.Client()
query = "SELECT COUNT(*) as total FROM `bigquery-public-data.thelook_ecommerce.orders`"
result = client.query(query).result().to_dataframe()
print(result)