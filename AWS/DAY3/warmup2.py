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
