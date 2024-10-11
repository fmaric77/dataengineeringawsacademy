





# Invoke your <user>-academy-lambda Lambda and use the Map state output as the Invoke state's input
# modify your Lambda to support the provided input




import json
import os
import awswrangler as wr
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import requests
import concurrent.futures
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
s3 = boto3.resource('s3')

# Environment variables
table_name_jobs = os.getenv('TABLE_NAME_JOBS', 'fmaric-academy-jobs')
bucket_name = os.getenv('BUCKET_NAME', 'fmaric-academy-aws')
dt_format = "%Y%m%dT%H%M%S.%f"

table_global = dynamodb.Table(os.getenv('TABLE_NAME_GLOBAL', 'fmaric-academy-global'))
table_jobs = dynamodb.Table(table_name_jobs)

def get_config():
    primary_key_globals = {
        'name': 'imdb-rest-api'
    }
    response = table_global.get_item(Key=primary_key_globals)
    partitions_url = response["Item"]["method"] + response["Item"]["host"] + "/" + response["Item"]["prefix"] + "/" + "partitions/"
    dataset_url = response["Item"]["method"] + response["Item"]["host"] + "/" + response["Item"]["prefix"] + "/" + "dataset/"
    return {
        'partitions_url': partitions_url,
        'dataset_url': dataset_url
    }

def fetch_partition_data(url):
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    response = session.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def fetch_and_upload_data(table_name, partition_name, url_dict):
    try:
        response_data = fetch_partition_data(url_dict['dataset_url'] + table_name + '?min_ingestion_dttm=' + partition_name)
        partition_data = json.dumps(response_data).encode('utf-8')
        s3_client.put_object(Bucket=bucket_name, Key=f'imdb/landing/{table_name}/{partition_name}.json', Body=partition_data, ContentType='application/json')
    except Exception as e:
        print(f"Error fetching and uploading data for {table_name} - {partition_name}: {e}")

def download_json_files(table_name, partitions, url_dict):
    latest_dttm = datetime.strptime(partitions[0], dt_format)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_and_upload_data, table_name, partition_name, url_dict) for partition_name in partitions]
        for future in concurrent.futures.as_completed(futures):
            partition_name = future.result()
            dt = datetime.strptime(partition_name, dt_format)
            if dt > latest_dttm:
                latest_dttm = dt
    return latest_dttm

def update_dynamodb_item(table_name, latest_dttm):
    tmp = 'min_ingestion_dttm: ' + str(latest_dttm)
    table_jobs.update_item(
        Key={
            'table_name': table_name
        },
        AttributeUpdates={
            'params': {
                'Value': tmp
            }
        }
    )

def process_job(job, url_dict):
    table_name = job['table_name']
    response_partition = fetch_partition_data(url_dict['partitions_url'] + table_name)
    partitions = response_partition
    latest_dttm = download_json_files(table_name, partitions, url_dict)
    update_dynamodb_item(table_name, latest_dttm)

def lambda_handler(event, context):
    url_dict = get_config()
    response_jobs = table_jobs.scan()
    jobs = response_jobs['Items']
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda job: process_job(job, url_dict), jobs)
   
{
  "Comment": "A description of my state machine",
  "StartAt": "Scan",
  "States": {
    "Scan": {
      "Type": "Task",
      "Parameters": {
        "TableName": "fmaric-academy-jobs"
      },
      "Resource": "arn:aws:states:::aws-sdk:dynamodb:scan",
      "Next": "Map"
    },
    "Map": {
      "Type": "Map",
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "INLINE"
        },
        "StartAt": "GetAndUpdate",
        "States": {
          "GetAndUpdate": {
            "Type": "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "OutputPath": "$.Payload",
            "Parameters": {
              "Payload.$": "$",
              "FunctionName": "arn:aws:lambda:eu-central-1:381492288052:function:fmaric-academy-lambda:$LATEST"
            },
            "Retry": [
              {
                "ErrorEquals": [
                  "Lambda.ServiceException",
                  "Lambda.AWSLambdaException",
                  "Lambda.SdkClientException",
                  "Lambda.TooManyRequestsException"
                ],
                "IntervalSeconds": 1,
                "MaxAttempts": 3,
                "BackoffRate": 2
              }
            ],
            "End": true
          }
        }
      },
      "End": true,
      "ItemsPath": "$.Items"
    }
  }
}





### Detailed Workflow:

# 1. **DynamoDB Table Scan**:
#    - The Step Function starts by scanning the [`fmaric-academy-jobs`](command:_github.copilot.openSymbolFromReferences?%5B%22fmaric-academy-jobs%22%2C%5B%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22c%3A%5C%5CUsers%5C%5CAcademy2024%5C%5CDesktop%5C%5Cfmaric%5C%5CAWS%5C%5CDAY3%5C%5C2.py%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fc%253A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22path%22%3A%22%2Fc%3A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22scheme%22%3A%22file%22%7D%2C%22pos%22%3A%7B%22line%22%3A76%2C%22character%22%3A23%7D%7D%5D%5D "Go to definition") DynamoDB table.

# 2. **Map State**:
#    - The Step Function uses a Map state to process each job item from the scan result.

# 3. **Lambda Invocation**:
#    - For each job item, the Step Function invokes the [`fmaric-academy-lambda`](command:_github.copilot.openSymbolFromReferences?%5B%22fmaric-academy-lambda%22%2C%5B%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22c%3A%5C%5CUsers%5C%5CAcademy2024%5C%5CDesktop%5C%5Cfmaric%5C%5CAWS%5C%5CDAY3%5C%5C2.py%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fc%253A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22path%22%3A%22%2Fc%3A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22scheme%22%3A%22file%22%7D%2C%22pos%22%3A%7B%22line%22%3A76%2C%22character%22%3A23%7D%7D%5D%5D "Go to definition") Lambda function.

# 4. **Lambda Function Execution**:
#    - The Lambda function fetches partition data from the [`url_partitions`](command:_github.copilot.openSymbolFromReferences?%5B%22url_partitions%22%2C%5B%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22c%3A%5C%5CUsers%5C%5CAcademy2024%5C%5CDesktop%5C%5Cfmaric%5C%5CAWS%5C%5CDAY3%5C%5C2.py%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fc%253A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22path%22%3A%22%2Fc%3A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22scheme%22%3A%22file%22%7D%2C%22pos%22%3A%7B%22line%22%3A79%2C%22character%22%3A4%7D%7D%5D%5D "Go to definition") API.
#    - It then fetches and uploads data from the [`url_data`](command:_github.copilot.openSymbolFromReferences?%5B%22url_data%22%2C%5B%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22c%3A%5C%5CUsers%5C%5CAcademy2024%5C%5CDesktop%5C%5Cfmaric%5C%5CAWS%5C%5CDAY3%5C%5C2.py%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fc%253A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22path%22%3A%22%2Fc%3A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22scheme%22%3A%22file%22%7D%2C%22pos%22%3A%7B%22line%22%3A80%2C%22character%22%3A4%7D%7D%5D%5D "Go to definition") API to the [`fmaric-academy-aws`](command:_github.copilot.openSymbolFromReferences?%5B%22fmaric-academy-aws%22%2C%5B%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22c%3A%5C%5CUsers%5C%5CAcademy2024%5C%5CDesktop%5C%5Cfmaric%5C%5CAWS%5C%5CDAY3%5C%5C2.py%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fc%253A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22path%22%3A%22%2Fc%3A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22scheme%22%3A%22file%22%7D%2C%22pos%22%3A%7B%22line%22%3A76%2C%22character%22%3A23%7D%7D%5D%5D "Go to definition") S3 bucket.
#    - The Lambda function updates the [`fmaric-academy-jobs`](command:_github.copilot.openSymbolFromReferences?%5B%22fmaric-academy-jobs%22%2C%5B%7B%22uri%22%3A%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22c%3A%5C%5CUsers%5C%5CAcademy2024%5C%5CDesktop%5C%5Cfmaric%5C%5CAWS%5C%5CDAY3%5C%5C2.py%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fc%253A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22path%22%3A%22%2Fc%3A%2FUsers%2FAcademy2024%2FDesktop%2Ffmaric%2FAWS%2FDAY3%2F2.py%22%2C%22scheme%22%3A%22file%22%7D%2C%22pos%22%3A%7B%22line%22%3A76%2C%22character%22%3A23%7D%7D%5D%5D "Go to definition") DynamoDB table with the latest ingestion datetime.

