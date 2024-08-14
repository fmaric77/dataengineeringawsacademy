import json
import boto3
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

partitions_url = "https://xtpc22s81a.execute-api.eu-central-1.amazonaws.com/v1/imdb/partitions"
specific_item_url = "https://xtpc22s81a.execute-api.eu-central-1.amazonaws.com/v1/imdb/dataset"
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
bucket_name = "fmaric-academy-aws"
table_name_globals = 'fmaric-academy-global'
table_name_jobs = 'fmaric-academy-jobs'
dt_format = "%Y%m%dT%H%M%S.%f"

def fetch_job_data(table_jobs, item):
    primary_key_jobs = {"table_name": item}
    return table_jobs.get_item(Key=primary_key_jobs)

def fetch_partition_data(table_name):
    response = requests.get(f"{partitions_url}/{table_name}")
    return response.json()

def fetch_specific_item_data(table_name, doc):
    url = f"{specific_item_url}/{table_name}?min_ingestion_dttm={doc}"
    response = requests.get(url)
    return response.json()

def upload_to_s3(table_name, doc, data):
    s3_path = f'imdb/landing/{table_name}/{doc}.json'
    data_bytes = bytes(json.dumps(data), 'utf-8')
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_path,
        Body=data_bytes,
        ContentType='application/json'
    )

def lambda_handler(event, context):
    primary_key_globals = {'name': 'imdb-rest-api'}
    table_global = dynamodb.Table(table_name_globals)
    table_jobs = dynamodb.Table(table_name_jobs)
    
    response = table_global.get_item(Key=primary_key_globals)
    jobs = response["Item"]["jobs"]

    joined_string = ''.join(jobs)
    normalized_string = joined_string.replace('\\"', '"')
    normal_list = json.loads(normalized_string)
    
    documents = []
    with ThreadPoolExecutor() as executor:
        job_futures = [executor.submit(fetch_job_data, table_jobs, item) for item in normal_list]
        for future in as_completed(job_futures):
            documents.append(future.result())
    
    with ThreadPoolExecutor() as executor:
        partition_futures = [executor.submit(fetch_partition_data, item["Item"]["table_name"]) for item in documents]
        partition_data = [future.result() for future in as_completed(partition_futures)]
        
        for index, item in enumerate(documents):
            table_name = item["Item"]["table_name"]
            data_partitions = partition_data[index]
            latest_date = datetime.strptime(data_partitions[0], dt_format)
            
            for doc in data_partitions:
                dt1 = datetime.strptime(doc, dt_format)
                if dt1 > latest_date:
                    latest_date = dt1
                
                data = fetch_specific_item_data(table_name, doc)
                executor.submit(upload_to_s3, table_name, doc, data)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }




# Compute Duration:

# Execution time per request: 300 seconds
# Memory allocated: 128 MB (0.125 GB)
# Compute duration per request: 300 seconds * 0.125 GB = 37.5 GB-seconds
# Monthly Compute Duration:

# Total executions per month: 1000
# Total compute duration: 1000 * 37.5 GB-seconds = 37,500 GB-seconds
# Cost Calculation:

# AWS Lambda pricing (as of the latest update): $0.00001667 per GB-second
# Monthly cost: 37,500 GB-seconds * $0.00001667 = $0.625125
# So, the total monthly Lambda execution cost is approximately $0.63.

# Additional Costs to Consider
# API Requests: Cost of making HTTP requests to the IMDb API.
# S3 Storage: Cost of storing the JSON responses in the S3 bucket.
# DynamoDB: Cost of reading from and writing to DynamoDB tables.
# Data Transfer: Cost of data transfer between AWS services (e.g., Lambda to S3, Lambda to DynamoDB).
# Strategies to Reduce Execution Time
# Parallel Processing: Use ThreadPoolExecutor to parallelize HTTP requests and S3 uploads, as already implemented.
# Batch Processing: Fetch and process data in batches to reduce the number of API calls and DynamoDB reads.
# Optimize Code: Ensure the code is optimized for performance, avoiding unnecessary computations and I/O operations.
# Increase Memory Allocation: Increasing the memory allocation can lead to faster execution times, as Lambda allocates more CPU power with more memory. However, this will increase the cost per GB-second.
# Impact on Costs
# Parallel Processing: Reduces execution time, potentially lowering the compute duration cost. However, it may increase the number of concurrent executions, which could impact the API rate limits and DynamoDB read/write capacity.
# Batch Processing: Reduces the number of API calls and DynamoDB reads, lowering the associated costs.
# Optimize Code: Reduces execution time, lowering the compute duration cost.
# Increase Memory Allocation: May reduce execution time but increases the cost per GB-second. The overall cost impact depends on the balance between reduced execution time and increased memory cost.