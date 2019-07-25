import boto3

CONFIG = dict()

CONFIG['aws_access_key_id'] = 'minioaccess'
CONFIG['aws_secret_access_key'] = 'miniosecret'
CONFIG['endpoint_url'] = 'http://minio:9000'

UNPROCESSED_BUCKET = 'unprocessed'
PROCESSED_BUCKET = 'processed'

client = boto3.client('s3', **CONFIG)
