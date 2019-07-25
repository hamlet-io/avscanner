import boto3
import os

CONFIG = dict()

CONFIG['aws_access_key_id'] = os.environ['AWS_S3_ACCESS_KEY_ID']
CONFIG['aws_secret_access_key'] = os.environ['AWS_S3_SECRET_ACCESS_KEY']
CONFIG['endpoint_url'] = os.environ['AWS_S3_ENDPOINT_URL']

UNPROCESSED_BUCKET = os.environ['UNPROCESSED_BUCKET_NAME']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET_NAME']

client = boto3.client('s3', **CONFIG)
