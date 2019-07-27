import os
import json
import boto3
from botocore.exceptions import ClientError
import pytest


S3_CONFIG = dict(
    endpoint_url=os.environ['AWS_S3_ENDPOINT_URL'],
    aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY']
)

UNPROCESSED_BUCKET_NAME = os.environ['UNPROCESSED_BUCKET_NAME']


@pytest.fixture
def fill_buckets():
    client = boto3.client(
        's3',
        **S3_CONFIG
    )
    dirname = 'tests/data/files'
    for filename in os.listdir(dirname):
        with open(os.path.join(dirname, filename), 'rb') as f:
            client.put_object(
                Key=filename.replace('-', '/'),
                Bucket='unprocessed',
                Body=f
            )


@pytest.fixture
def clear_buckets():
    s3 = boto3.resource(
        's3',
        **S3_CONFIG
    )
    processed = s3.Bucket(os.environ['PROCESSED_BUCKET_NAME'])
    unprocessed = s3.Bucket(os.environ['UNPROCESSED_BUCKET_NAME'])
    processed.objects.all().delete()
    unprocessed.objects.all().delete()


@pytest.fixture
def s3_events_dict():
    dirname = 'tests/data/events/put'
    events = dict(put=dict())
    client = boto3.client('s3', **S3_CONFIG)
    for filename in os.listdir(dirname):
        with open(os.path.join(dirname, filename)) as f:
            name, extension = os.path.splitext(filename)
            event = json.loads(f.read())
            events['put'][name] = event
            try:
                response = client.get_object(
                    Bucket=UNPROCESSED_BUCKET_NAME,
                    Key=filename.replace('-', '/')
                )
                # updating event props
                event = event['Records'][0]
                event['s3']['object']['eTag'] = response['ETag']
                event['s3']['object']['size'] = response['ContentLength']
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    pass
    return events
