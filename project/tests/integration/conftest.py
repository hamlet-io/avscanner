import os
import boto3
import pytest

ARCHIVE_BUCKET = os.environ['ARCHIVE_BUCKET_NAME']
UNPROCESSED_BUCKET = os.environ['UNPROCESSED_BUCKET_NAME']
QUARANTINE_BUCKET = os.environ['QUARANTINE_BUCKET_NAME']

VALID_BUCKETS = [
    ARCHIVE_BUCKET,
    UNPROCESSED_BUCKET,
    QUARANTINE_BUCKET
]

S3_CONNECTION_DATA = dict(
    aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
    endpoint_url=os.environ['AWS_S3_ENDPOINT_URL']
)


def create_buckets():
    s3 = boto3.resource('s3', **S3_CONNECTION_DATA)
    exceptions = s3.meta.client.exceptions

    for bucket in s3.buckets.all():
        if bucket.name not in VALID_BUCKETS:
            bucket.objects.delete()
            bucket.delete()

    def create(name):
        try:
            s3.Bucket(name).create()
        except exceptions.BucketAlreadyOwnedByYou:
            pass

    for name in VALID_BUCKETS:
        create(name)


@pytest.fixture(scope='function')
def clear_buckets():
    s3 = boto3.resource('s3', **S3_CONNECTION_DATA)

    def clear(name):
        s3.Bucket(name).objects.all().delete()

    for name in VALID_BUCKETS:
        clear(name)


def pytest_sessionstart():
    create_buckets()
