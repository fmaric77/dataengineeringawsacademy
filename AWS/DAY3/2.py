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
    table_name_global = 'fmaric-academy-global'
    table_name_jobs = 'fmaric-academy-jobs'
    bucket_name = 'fmaric-academy-aws'
    table_global = dynamodb.Table(table_name_global)
    table_jobs = dynamodb.Table(table_name_jobs)
    url_partitions = 'https://xtpc22s81a.execute-api.eu-central-1.amazonaws.com/v1/imdb/partitions/'
    url_data = 'https://xtpc22s81a.execute-api.eu-central-1.amazonaws.com/v1/imdb/dataset/'
    bucket = s3.Bucket(bucket_name)
    dt_format = "%Y%m%dT%H%M%S.%f"
    
    response_global = table_global.get_item(
        Key = {
            'name': 'imdb-rest-api'
        }
    )
    jobs = response_global['Item']['jobs']
    
    joined_string = ''.join(jobs)
    normalized_string = joined_string.replace('\\"', '"')
    normal_list_jobs = json.loads(normalized_string)

    def fetch_partition_data(url):
        response = requests.get(url)
        return response.json()

    def fetch_and_upload_data(table_name, partition_name):
        response_data = fetch_partition_data(url_data + table_name + '?min_ingestion_dttm=' + partition_name)
        partition_data = bytes(json.dumps(response_data), 'utf-8')
        s3_client.put_object(Bucket=bucket_name, Key=f'imdb/landing/{table_name}/{partition_name}.json', Body=partition_data, ContentType='application/json')

    def process_job(job):
        response_jobs = table_jobs.get_item(
            Key = {
                'table_name': job
            }
        )
        table_name = response_jobs['Item']['table_name']
        
        response_partition = fetch_partition_data(url_partitions + table_name)
        partitions = response_partition
        
        latest_dttm = datetime.strptime(partitions[0], dt_format)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(fetch_and_upload_data, table_name, partition_name) for partition_name in partitions]
            for future in concurrent.futures.as_completed(futures):
                partition_name = future.result()
                dt = datetime.strptime(partition_name, dt_format)
                if dt > latest_dttm:
                    latest_dttm = dt
        
        tmp = 'min_ingestion_dttm: ' + str(latest_dttm)
        table_jobs.update_item(
            TableName=table_name_jobs,
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
        executor.map(process_job, normal_list_jobs)