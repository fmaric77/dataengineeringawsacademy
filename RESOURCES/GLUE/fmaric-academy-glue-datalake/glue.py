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
    database="fmaric-academy-aws-landing-cf",
    table_name="name_basics",
    transformation_ctx="name_basics_df"
).toDF()

title_basics_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing-cf",
    table_name="title_basics",
    transformation_ctx="title_basics_df"
).toDF()

title_crew_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing-cf",
    table_name="title_crew",
    transformation_ctx="title_crew_df"
).toDF()

title_episode_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing-cf",
    table_name="title_episode",
    transformation_ctx="title_episode_df"
).toDF()

title_principals_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing-cf",
    table_name="title_principals",
    transformation_ctx="title_principals_df"
).toDF()

title_ratings_df = glueContext.create_dynamic_frame.from_catalog(
    database="fmaric-academy-aws-landing-cf",
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
name_basics_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws-cf/datalake/name_basics/")
title_basics_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws-cf/datalake/title_basics/")
title_crew_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws-cf/datalake/title_crew/")
title_episode_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws-cf/datalake/title_episode/")
title_principals_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws-cf/datalake/title_principals/")
title_ratings_df.write.partitionBy("datalake_date").mode("overwrite").parquet("s3://fmaric-academy-aws-cf/datalake/title_ratings/")

# Commit the job
job.commit()