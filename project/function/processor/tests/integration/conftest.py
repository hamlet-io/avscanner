import os
import json
import boto3
import pytest


S3_CONFIG = dict(
    endpoint_url=os.environ['AWS_S3_ENDPOINT_URL'],
    aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY']
)


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


@pytest.fixture(scope='session')
def s3_events_dict():
    dirname = 'tests/data/events'
    events = dict()
    for filename in os.listdir(dirname):
        with open(os.path.join(dirname, filename)) as f:
            name, extension = os.path.splitext(filename)
            events[name] = json.loads(f.read())
    return events
