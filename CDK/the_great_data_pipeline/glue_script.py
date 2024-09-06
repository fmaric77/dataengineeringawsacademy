import boto3

# Initialize S3 client
s3 = boto3.client('s3')

# Specify the bucket name and prefix (folder) to scan
bucket_name = "fmaric-bucket-cdk"
prefix = "input-data/"

# List all objects in the specified S3 bucket and prefix
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

# Extract and print the file names (keys)
if 'Contents' in response:
    for obj in response['Contents']:
        print(f"Found file: {obj['Key']}")
else:
    print("No files found.")