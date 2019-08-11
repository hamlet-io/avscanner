import os
import io
import subprocess
import shutil
import string
import json
import posixpath
import boto3
import pytest


TEMP_DIR = '/tmp'
TEST_FILES_DIR = 'tests/data/file'
TEST_PUT_EVENT_TEMPLATE_FILE = 'tests/data/event/put/template.json'


ARCHIVE_BUCKET = os.environ['ARCHIVE_BUCKET_NAME']
UNPROCESSED_BUCKET = os.environ['UNPROCESSED_BUCKET_NAME']
QUARANTINE_BUCKET = os.environ['QUARANTINE_BUCKET_NAME']

VALID_BUCKETS = [
    ARCHIVE_BUCKET,
    UNPROCESSED_BUCKET,
    QUARANTINE_BUCKET
]

VALIDATION_QUEUE = os.environ['VALIDATION_QUEUE_NAME']
VIRUS_SCANNING_QUEUE = os.environ['VIRUS_SCANNING_QUEUE_NAME']

VALID_QUEUES = [
    VALIDATION_QUEUE,
    VIRUS_SCANNING_QUEUE
]

S3_CONNECTION_DATA = dict(
    aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
    endpoint_url=os.environ['AWS_S3_ENDPOINT_URL'],
    region_name=os.environ['AWS_S3_REGION']
)


SQS_CONNECTION_DATA = dict(
    aws_access_key_id=os.environ['AWS_SQS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SQS_SECRET_ACCESS_KEY'],
    endpoint_url=os.environ['AWS_SQS_ENDPOINT_URL'],
    region_name=os.environ['AWS_SQS_REGION']
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


@pytest.fixture(scope='session')
def clear_queues():
    def fixture():
        sqs = boto3.resource('sqs', **SQS_CONNECTION_DATA)

        def clear(name):
            queue = sqs.get_queue_by_name(
                QueueName=name
            )
            queue.purge()

        for queue in VALID_QUEUES:
            clear(queue)
    return fixture


@pytest.fixture(scope='session')
def clear_buckets():
    def fixture():
        s3 = boto3.resource('s3', **S3_CONNECTION_DATA)

        def clear(name):
            s3.Bucket(name).objects.all().delete()

        for name in VALID_BUCKETS:
            clear(name)
    return fixture


@pytest.fixture(scope='session')
def fill_unprocessed_bucket():
    with open(TEST_PUT_EVENT_TEMPLATE_FILE) as f:
        template = string.Template(f.read())

    def fixture():
        put = dict()
        s3 = boto3.resource('s3', **S3_CONNECTION_DATA)
        files = os.listdir(TEST_FILES_DIR)
        for filename in files:
            # writing file to bucket
            realname = os.path.join(TEST_FILES_DIR, filename)
            key = posixpath.join(*filename.split('-'))
            bucket = s3.Bucket(name=UNPROCESSED_BUCKET)
            with open(realname, 'rb') as f:
                body = f.read()
                bucket.put_object(
                    Key=key,
                    Body=io.BytesIO(body)
                )
            # creating event
            obj = bucket.Object(key=key)
            event_text = template.substitute(
                size=obj.content_length,
                etag=obj.e_tag.replace('"', ''),  # etag for some reason contains ""
                bucket=UNPROCESSED_BUCKET,
                key=obj.key
            )
            put[obj.key] = json.loads(event_text)
        return dict(put=put)
    return fixture


@pytest.fixture(scope='session')
def clear_tmp():
    def fixture():
        stat = os.stat(TEMP_DIR)
        shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.chmod(TEMP_DIR, stat.st_mode)
        os.chown(TEMP_DIR, stat.st_uid, stat.st_gid)
    return fixture


def check_clamdscan():
    result = subprocess.run(
        [
            'clamdscan',
            os.path.abspath(__file__)
        ],
        capture_output=True,
        encoding='utf8'
    )
    if result.stderr:
        raise RuntimeError(f'Clamd not initialized:\n{result.stderr}')


def pytest_sessionstart():
    check_clamdscan()
    create_buckets()
