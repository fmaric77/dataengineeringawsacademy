from aws_cdk import (
    aws_glue as glue,
    aws_iam as iam,
    aws_cloudwatch as cloudwatch,
    Duration,
    Stack
)
from constructs import Construct

class ProcessingStack(Stack):

    def __init__(self, scope: Construct, id: str, ingestion_stack: Stack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        data_ingestion_bucket = ingestion_stack.data_ingestion_bucket

        glue_role = iam.Role(self, "GlueJobRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
            ]
        )

        data_ingestion_bucket.grant_read(glue_role)

        glue_job = glue.CfnJob(self, "DataAlchemistsJob",
            role=glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                script_location="s3://fmaric-bucket-cdk/glue_script.py",
                python_version="3"
            ),
            default_arguments={
                "--extra-py-files": "s3://fmaric-bucket-cdk/dependencies.zip"
            },
            max_retries=1
        )

        cloudwatch.Alarm(self, "GlueJobFailureAlarm",
            metric=cloudwatch.Metric(
                namespace="Glue",
                metric_name="GlueJobRun",
                dimensions_map={
                    "JobName": glue_job.ref
                },
                statistic="sum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
        )