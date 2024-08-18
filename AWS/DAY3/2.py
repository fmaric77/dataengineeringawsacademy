# FIXME: only one lambda_handler function can be inside a file, move warmup-1 and 2 into a separate files

# Warmup task
# The main idea for this task is to give you a better explanation what orchestration of services means and how to "chain services together".

# Orchestrate two lambdas with a Step function to make output of the first lambda input for the second one.

# Create a <user>-academy-warmup-lambda-1 and in AWS console add code which returns the sum of two randomly selected numbers and print the result
import json
import random

def lambda_handler(event, context):
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)
    result = num1 + num2
    
    print(f"The sum of {num1} and {num2} is {result}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }

# Create a <user>-academy-warmup-lambda-2 and in AWS console add code which takes a number from event and adds it to a randomly selected number and print the result
import json
import random

def lambda_handler(event, context):
    input_number = int(event['body'])  
    random_number = random.randint(1, 100)
    result = input_number + random_number
    
    print(f"Adding {input_number} to {random_number} gives {result}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }


# Create a <user>-academy-aws-statemachine-warmup Step Function
# Edit the Step function definition and chain two lambdas together so the output of the first lambda can be input for the second lambda
{
  "Comment": "A warmup step function that chains two lambdas together",
  "StartAt": "Lambda1",
  "States": {
    "Lambda1": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-central-1:381492288052:function:fmaric-acadmey-warmup-lamba-1:$LATEST",
      "Next": "Lambda2"
    },
    "Lambda2": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-central-1:381492288052:function:fmaric-academy-warmup-lambda-2:$LATEST",
      "End": true
    }
  }
}



# Invoke your <user>-academy-lambda Lambda and use the Map state output as the Invoke state's input
# modify your Lambda to support the provided input


import json
import awswrangler as wr
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import requests
import concurrent.futures

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
s3 = boto3.resource('s3')

def lambda_handler(event, context):
    # FIXME: these variables needs to be outside of lambda_handler and moved into a environment variables
    table_name_jobs = 'fmaric-academy-jobs'
    bucket_name = 'fmaric-academy-aws'
    table_jobs = dynamodb.Table(table_name_jobs)
    # FIXME: these variables needs to be extracted from dynamodb global variables
    url_partitions = 'https://xtpc22s81a.execute-api.eu-central-1.amazonaws.com/v1/imdb/partitions/'
    url_data = 'https://xtpc22s81a.execute-api.eu-central-1.amazonaws.com/v1/imdb/dataset/'
    dt_format = "%Y%m%dT%H%M%S.%f"

    response_jobs = table_jobs.scan()
    jobs = response_jobs['Items']

    def fetch_partition_data(url):
        # FIXME: need to add behavior for responses other than 200
        response = requests.get(url)
        return response.json()

    def fetch_and_upload_data(table_name, partition_name):
        response_data = fetch_partition_data(url_data + table_name + '?min_ingestion_dttm=' + partition_name)
        partition_data = bytes(json.dumps(response_data), 'utf-8')
        # FIXME: add try/except
        s3_client.put_object(Bucket=bucket_name, Key=f'imdb/landing/{table_name}/{partition_name}.json', Body=partition_data, ContentType='application/json')

    def process_job(job):
        table_name = job['table_name']
        
        response_partition = fetch_partition_data(url_partitions + table_name)
        partitions = response_partition
        
        # FIXME: move downloading of JSON file for each parition in a separate function
        latest_dttm = datetime.strptime(partitions[0], dt_format)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(fetch_and_upload_data, table_name, partition_name) for partition_name in partitions]
            for future in concurrent.futures.as_completed(futures):
                partition_name = future.result()
                dt = datetime.strptime(partition_name, dt_format)
                if dt > latest_dttm:
                    latest_dttm = dt
        
        # FIXME: move to separate function
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

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_job, jobs)

# Great work with your effort to make code more efficient. You showed very high level of python knowledge

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

