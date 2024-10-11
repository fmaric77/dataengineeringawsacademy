
# Razgovor je otvoren. 1 pročitana poruka.

# Preskoči na sadržaj
# Koristite Gmail sa čitačima zaslona
# Razgovori
# Iskorišteno 3,8 GB od 15 GB
# Uvjeti · Privatnost · Pravila o programu
# Zadnja aktivnost na računu: prije 1 minutu
# Otvoreno na još jednoj lokaciji · Pojedinosti
# select * FROM "AwsDataCatalog"."fmaric-academy-aws-landing"."title_ratings" limit 10
# Time in queue:
# 73 ms
# Run time:
# 2.697 sec
# Data scanned:
# 77.49 MB


# select * FROM "AwsDataCatalog"."fmaric-aws-datalake"."title_ratings" limit 10
# Time in queue:
# 96 ms
# Run time:
# 1.103 sec
# Data scanned:
# 66.63 KB

# Parquet-based queries have a more than two times faster run time. 



# AWS Glue Job Cost:
# DPU Cost: Approximately $0.44 per DPU-hour 
# Job Duration: 1.5 hours (90 minutes).
# DPU Usage: 10 DPUs.
# Monthly Cost=1.5×10×0.44×30=$198

# AWS Glue Crawler Cost:
# DPU Cost: $0.44 per DPU-hour.
# Crawlers: 2 crawlers, each with 2 DPUs.
# If each crawler runs for 1 hour daily:
# Monthly Cost for Crawlers=2×2×0.44×30=$52.80

# Cost Impact: Increasing DPUs will increase the cost linearly, as the cost is directly proportional to the number of DPUs.

# Performance Impact: More DPUs can decrease job execution time, particularly for large datasets, improving overall performance. However, beyond a certain point, adding more DPUs may have diminishing returns.



#JOB script

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import pyspark.sql.functions as F

# Initialize Glue job and context
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Load data from AWS Glue Data Catalog
name_basics_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing",
    table_name="name_basics",
    transformation_ctx="name_basics_df"
).toDF()

title_basics_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing",
    table_name="title_basics",
    transformation_ctx="title_basics_df"
).toDF()

title_crew_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing",
    table_name="title_crew",
    transformation_ctx="title_crew_df"
).toDF()

title_episode_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing",
    table_name="title_episode",
    transformation_ctx="title_episode_df"
).toDF()

title_principals_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing",
    table_name="title_principals",
    transformation_ctx="title_principals_df"
).toDF()

title_ratings_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing",
    table_name="title_ratings",
    transformation_ctx="title_ratings_df"
).toDF()

# Add new columns (datalake_timestamp and datalake_date)
def add_datalake_columns(df):
    return df.withColumn("datalake_timestamp", F.current_timestamp())\
             .withColumn("datalake_date", F.current_date())

name_basics_df = add_datalake_columns(name_basics_df)
title_basics_df = add_datalake_columns(title_basics_df)
title_crew_df = add_datalake_columns(title_crew_df)
title_episode_df = add_datalake_columns(title_episode_df)
title_principals_df = add_datalake_columns(title_principals_df)
title_ratings_df = add_datalake_columns(title_ratings_df)

# Write data to S3 in parquet format, partitioned by datalake_date
name_basics_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws/datalake/name_basics/")
title_basics_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws/datalake/title_basics/")
title_crew_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws/datalake/title_crew/")
title_episode_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws/datalake/title_episode/")
title_principals_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws/datalake/title_principals/")
title_ratings_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws/datalake/title_ratings/")

# Commit the job
job.commit()



#lambda


import json
import boto3
from datetime import datetime
import requests

dynamodb_resource = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
s3_client = boto3.client('s3')

def get_global_configuration():
    table = dynamodb_resource.Table('fmaric-academy-global')
    response = table.get_item(
        Key= {
            'name': 'imdb-rest-api',
        }
    )
    item = response['Item']
    return item

def save_to_s3(data, table_name):
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%S.%f')
    s3_path = f"imdb/landing/{table_name}/{timestamp}.json"
    data_bytes = bytes(data, "UTF-8")
    s3_client.put_object(
        Bucket='fmaric-academy-aws',
        Key=s3_path,
        Body=data_bytes,
        ContentType='application/json'
    )

def update_jobs(job_name, current_time):
    table = dynamodb_resource.Table('fmaric-academy-jobs')
    ingestion_dttm = json.dumps({"min_ingestion_dttm": current_time})
    table.update_item(
        Key={
            'table_name': job_name
        },
        UpdateExpression='SET params = :time',
        ExpressionAttributeValues={
            ':time': ingestion_dttm
        }
    )

def lambda_handler(event, context):
    job = event.get('table_name')
    job_name = job['S']

    global_config = get_global_configuration()
   
    base_url = global_config['url'].format(
        method=global_config['method'],
        host=global_config['host'],
        port=global_config['port'],
        prefix=global_config['prefix']
    )
   
    full_url_partitions = base_url + global_config['partitions_uri']
    full_url_partitions = full_url_partitions.format(table_name=job_name)
    response_partition = requests.get(full_url_partitions)
    data = response_partition.json()

    for partition_number in data:
        specific_url = f"{base_url}/dataset/{job_name}?min_ingestion_dttm={partition_number}"
        specific_partition_response = requests.get(specific_url)
        specific_partition_data = specific_partition_response.json()
        save_to_s3(specific_partition_data, job_name)

    current_time = datetime.now().strftime('%Y%m%dT%H%M%S')
    update_jobs(job_name, current_time)

    return {
        'statusCode': 200,
        'body': json.dumps('Ingestion completed successfully!')
    }

