import boto3

# Initialize S3 client
s3 = boto3.client('s3')

bucket_name = "fmaric-bucket-cdk"
prefix = "input-data/"

response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

if 'Contents' in response:
    for obj in response['Contents']:
        print(f"Found file: {obj['Key']}")
else:
    print("No files found.")