from aws_cdk import (
    aws_s3 as s3,
    RemovalPolicy,
    Stack
)
from constructs import Construct

class IngestionStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.data_ingestion_bucket = s3.Bucket(self, "DataIngestionVault",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY
        )