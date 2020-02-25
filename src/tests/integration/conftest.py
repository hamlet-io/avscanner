import os
import pytz
import io
import urllib
import datetime
import subprocess
import shutil
import string
import json
import hashlib
import posixpath
import boto3
import pytest


TEMP_DIR = '/tmp'
TEST_FILES_DIR = 'tests/data/file'
TEST_PUT_EVENT_TEMPLATE_FILE = 'tests/data/event/put/template.json'


ARCHIVE_BUCKET = os.environ['ARCHIVE_BUCKET_NAME']
UNPROCESSED_BUCKET = os.environ['UNPROCESSED_BUCKET_NAME']
QUARANTINE_BUCKET = os.environ['QUARANTINE_BUCKET_NAME']
ARCHIVE_TIMEZONE = os.environ['ARCHIVE_TIMEZONE']

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

VIRUS_NOTIFICATION_TOPIC = os.environ.get('VIRUS_NOTIFICATION_TOPIC_ARN')

VALID_TOPICS = [
    VIRUS_NOTIFICATION_TOPIC
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

SNS_CONNECTION_DATA = dict(
    aws_access_key_id=os.environ['AWS_SNS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SNS_SECRET_ACCESS_KEY'],
    endpoint_url=os.environ['AWS_SNS_ENDPOINT_URL'],
    region_name=os.environ['AWS_SNS_REGION']
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


def create_queues():
    sqs = boto3.resource('sqs', **SQS_CONNECTION_DATA)
    exceptions = sqs.meta.client.exceptions
    for queue in sqs.queues.all():
        name = queue.attributes['QueueArn'].split(':')[-1]
        if name in VALID_QUEUES:
            queue.purge()
        else:
            queue.delete()
    for name in VALID_QUEUES:
        try:
            sqs.create_queue(QueueName=name)
        except exceptions.QueueNameExists:
            pass


# creating sns topics
def create_topics():
    sns = boto3.resource('sns', **SNS_CONNECTION_DATA)

    for arn in VALID_TOPICS:
        name = arn.split(':')[-1]
        topic = sns.create_topic(Name=name)
        assert topic.arn == arn


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


# localized datetime
def event_filename_to_event_time(filename):
    year, month, day, timestamp_offset, user, bucket_filename = filename.split('-')
    return pytz.timezone(ARCHIVE_TIMEZONE).localize(
        datetime.datetime(
            year=int(year),
            month=int(month),
            day=int(day),
        )
    )


# production like filename style
def isoformat_time_filename(eventTime, offset_seconds):
    return (eventTime + datetime.timedelta(seconds=offset_seconds)).isoformat()


# aws apmlify like key
def event_filename_to_unprocessed_key(filename):
    year, month, day, timestamp_offset, user, bucket_filename = filename.split('-')
    upload_hash = hashlib.md5(filename.encode()).hexdigest()[:7]
    eventTime = event_filename_to_event_time(filename)
    return posixpath.join(
        'private',
        user,
        'submissionInbox',
        '{}-{}.json'.format(isoformat_time_filename(eventTime, int(timestamp_offset)), upload_hash)
    )


# processed file key
def event_filename_to_archive_key(filename):
    year, month, day, timestamp_offset, user, bucket_filename = filename.split('-')
    upload_hash = hashlib.md5(filename.encode()).hexdigest()[:7]
    eventTime = event_filename_to_event_time(filename)
    return posixpath.join(
        str(eventTime.year),
        str(eventTime.month),
        str(eventTime.day),
        user,
        '{}-{}.json'.format(isoformat_time_filename(eventTime, int(timestamp_offset)), upload_hash)
    )


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
            year, month, day, user, timestamp_offset, bucket_filename = filename.split('-')
            realname = os.path.join(TEST_FILES_DIR, filename)
            eventTime = event_filename_to_event_time(filename)
            key = event_filename_to_unprocessed_key(filename)
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
                # aws uses urlencoded keys
                key=urllib.parse.quote(obj.key),
                eventTime=eventTime.isoformat()
            )
            put[filename] = json.loads(event_text)
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
    create_topics()
    create_queues()
