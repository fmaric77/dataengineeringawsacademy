from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_lambda_event_sources as event_sources,
)
from constructs import Construct

class ConfigurableDataHubFmaricStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Retrieve the environment context variable
        env = self.node.try_get_context('env')

        # Define resource configurations based on the environment
        if env == 'dev':
            dynamo_read_capacity = 1
            dynamo_write_capacity = 1
            lambda_memory_size = 128
        elif env == 'test':
            dynamo_read_capacity = 5
            dynamo_write_capacity = 5
            lambda_memory_size = 512
        else:
            raise ValueError("Invalid environment. Use 'dev' or 'test'.")

        # Create the DynamoDB table
        table = dynamodb.Table(self, "ArtifactsTableFmaric",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            read_capacity=dynamo_read_capacity,
            write_capacity=dynamo_write_capacity,
            stream=dynamodb.StreamViewType.NEW_IMAGE
        )

        # Create the Lambda function
        lambda_function = _lambda.Function(self, "ArtifactsProcessorFmaric",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset("lambda"),
            memory_size=lambda_memory_size,
            environment={
                "TABLE_NAME": table.table_name
            }
        )

        # Grant the Lambda function read/write permissions to the DynamoDB table
        table.grant_read_write_data(lambda_function)

        # Create an event source mapping for the Lambda function to be triggered by DynamoDB Streams
        lambda_function.add_event_source(event_sources.DynamoEventSource(table,
            starting_position=_lambda.StartingPosition.TRIM_HORIZON,
            batch_size=5,
            bisect_batch_on_error=True,
            retry_attempts=10
        ))