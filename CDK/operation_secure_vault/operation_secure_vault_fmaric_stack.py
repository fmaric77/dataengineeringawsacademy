from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy
)
from constructs import Construct

class OperationSecureVaultFmaricStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(self, "SecureVaultBucketFmaric",
            versioned=True, 
            encryption=s3.BucketEncryption.S3_MANAGED,  
            lifecycle_rules=[  
                s3.LifecycleRule(
                    id="TransitionToIAFmaric",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        )
                    ]
                ),
                s3.LifecycleRule(
                    id="ExpireOldVersionsFmaric",
                    noncurrent_version_expiration=Duration.days(365)
                )
            ],
            removal_policy=RemovalPolicy.DESTROY 
        )


        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:*"],
                resources=[self.bucket.bucket_arn, f"{self.bucket.bucket_arn}/*"],
                principals=[iam.AccountRootPrincipal()]
            )
        )