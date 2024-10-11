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