import json
import awswrangler
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
import requests
import os
from dataclasses import dataclass

@dataclass
class Config:
    dynamodb = boto3.resource('dynamodb')
    s3_client = boto3.client('s3')
    table_global = dynamodb.Table(os.environ['table_name_global'])
    table_jobs = dynamodb.Table(os.environ['table_name_jobs'])
    dt_format = "%Y%m%dT%H%M%S.%f"
    
    ##get base urls
    @staticmethod
    def getConfig():
        primary_key_globals = {
            'name': 'imdb-rest-api'
        }
        response = Config.table_global.get_item(Key=primary_key_globals)
        partitions_url = response["Item"]["method"] + response["Item"]["host"] + "/" + response["Item"]["prefix"] + "/" + "partitions/"
        dataset_url = response["Item"]["method"] + response["Item"]["host"] + "/" + response["Item"]["prefix"] + "/" + "dataset/"

        return {
            'partitions_url': partitions_url,
            'dataset_url': dataset_url
        }

##get all partitions for specified table name
def fetchPartitions(table_name, url):
    response_partition = requests.get(url+table_name)
    partitions = response_partition.json()
    
    return partitions

##update column
def update(table_name, updated_value, table):
    table.update_item(
        TableName = os.environ['table_name_jobs'],
        Key = {
            'table_name': table_name
        },
        AttributeUpdates = {
            'params': {
                'Value': updated_value
            }
        }
    )

##get json data for specified partition and transform it to bytes
def fetchPartitionsData(table_name, url_dict, partition_name):
    response_data = requests.get(url_dict['dataset_url']+table_name+'?min_ingestion_dttm='+partition_name)
    partition_data = response_data.json()
    partition_data = bytes(partition_data, 'utf-8')

    return partition_data

##save bytes data to s3 bucket
def saveToS3(partition_data, table_name, partition_name):
    try:
        Config.s3_client.put_object(Bucket=os.environ['bucket_name'], Key=f'imdb/landing/{table_name}/{partition_name}.json', Body=partition_data, ContentType='application/json')
    except Exception as e:
        print(e)

def lambda_handler(event, context):
    table_name = event['table_name']['S']
    
    url_dict = Config.getConfig()

    partitions = fetchPartitions(table_name, url_dict['partitions_url'])
    
    latest_dttm = datetime.strptime(partitions[0], Config.dt_format)
    for partition_name in partitions:
        dt = datetime.strptime(partition_name, Config.dt_format)
        if dt > latest_dttm:
            latest_dttm = dt
            
        partition_data = fetchPartitionsData(table_name, url_dict, partition_name)
        saveToS3(partition_data, table_name, partition_name)

    updated_row = 'min_ingestion_dttm: ' +str(latest_dttm)
    update(table_name, updated_row, Config.table_jobs)