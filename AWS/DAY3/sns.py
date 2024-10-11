import json
import boto3

sns_client = boto3.client('sns')

SNS_TOPIC_ARN = 'arn:aws:sns:eu-central-1:381492288052:fmaric-sns-academy-lambda'

def lambda_handler(event, context):
    try:
        message = event['Records'][0]['Sns']['Message']

        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject='SNS to Email'
        )
        print("Message sent to email:", response)

    except Exception as e:
        print(f"Error: {str(e)}")
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"An error occurred in the Lambda function: {str(e)}",
            Subject='Lambda Function Error'
        )
        
        raise e
