import os
import json
import pytest
import boto3
from botocore.exceptions import ClientError


S3_CONFIG = dict(
    endpoint_url=os.environ['AWS_S3_ENDPOINT_URL'],
    aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY']
)


UNPROCESSED_BUCKET = os.environ['UNPROCESSED_BUCKET_NAME']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET_NAME']
VALID_DIR = os.environ['VALID_DIR']
INVALID_DIR = os.environ['INVALID_DIR']
QUARANTINE_DIR = os.environ['QUARANTINE_DIR']


def filename_to_bucket_key(filename):
    return filename.replace('-', '/')


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
                Key=filename_to_bucket_key(filename),
                Bucket=UNPROCESSED_BUCKET,
                Body=f
            )


@pytest.fixture
def clear_buckets():
    s3 = boto3.resource(
        's3',
        **S3_CONFIG
    )
    processed = s3.Bucket(PROCESSED_BUCKET)
    unprocessed = s3.Bucket(UNPROCESSED_BUCKET)
    processed.objects.all().delete()
    unprocessed.objects.all().delete()


@pytest.fixture
def s3_events_dict():
    dirname = 'tests/data/events/put'
    events = dict(put=dict())
    client = boto3.client('s3', **S3_CONFIG)
    for filename in os.listdir(dirname):
        with open(os.path.join(dirname, filename)) as f:
            event = json.loads(f.read())
            events['put'][filename] = event
            try:
                response = client.get_object(
                    Bucket=UNPROCESSED_BUCKET,
                    Key=filename_to_bucket_key(filename)
                )
                # updating event props
                event = event['Records'][0]
                event['s3']['object']['eTag'] = response['ETag']
                event['s3']['object']['size'] = response['ContentLength']
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    pass
    return events


@pytest.fixture
def s3client():
    return boto3.client('s3', **S3_CONFIG)
