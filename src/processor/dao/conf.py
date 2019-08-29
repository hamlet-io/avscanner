import os


ARCHIVE_BUCKET = os.environ.get('ARCHIVE_BUCKET_NAME')
UNPROCESSED_BUCKET = os.environ.get('UNPROCESSED_BUCKET_NAME')
QUARANTINE_BUCKET = os.environ.get('QUARANTINE_BUCKET_NAME')

VALIDATION_QUEUE = os.environ.get('VALIDATION_QUEUE_NAME')
VIRUS_SCANNING_QUEUE = os.environ.get('VIRUS_SCANNING_QUEUE_NAME')

VIRUS_NOTIFICATION_TOPIC = os.environ.get('VIRUS_NOTIFICATION_TOPIC_ARN')

ARCHIVE_BUCKET_VALID_DIR = os.environ.get('ARCHIVE_BUCKET_VALID_DIR')
ARCHIVE_BUCKET_INVALID_DIR = os.environ.get('ARCHIVE_BUCKET_INVALID_DIR')
ARCHIVE_BUCKET_COMPRESSED_DIR = os.environ.get('ARCHIVE_BUCKET_COMPRESSED_DIR')


def get_s3_env_conf(**kwargs):
    data = dict()
    keys = {
        'AWS_S3_ACCESS_KEY_ID': 'aws_access_key_id',
        'AWS_S3_SECRET_ACCESS_KEY': 'aws_secret_access_key',
        'AWS_S3_ENDPOINT_URL': 'endpoint_url',
        'AWS_S3_REGION': 'region_name'
    }
    for env_key, conn_key in keys.items():
        try:
            data[conn_key] = os.environ[env_key]
        except KeyError:
            pass
    return data


def get_sqs_env_conf(**kwargs):
    data = dict()
    keys = {
        'AWS_SQS_ACCESS_KEY_ID': 'aws_access_key_id',
        'AWS_SQS_SECRET_ACCESS_KEY': 'aws_secret_access_key',
        'AWS_SQS_ENDPOINT_URL': 'endpoint_url',
        'AWS_SQS_REGION': 'region_name'
    }
    for env_key, conn_key in keys.items():
        try:
            data[conn_key] = os.environ[env_key]
        except KeyError:
            pass
    return data


def get_sns_env_conf(**kwargs):
    data = dict()
    keys = {
        'AWS_SNS_ACCESS_KEY_ID': 'aws_access_key_id',
        'AWS_SNS_SECRET_ACCESS_KEY': 'aws_secret_access_key',
        'AWS_SNS_ENDPOINT_URL': 'endpoint_url',
        'AWS_SNS_REGION': 'region_name'
    }
    for env_key, conn_key in keys.items():
        try:
            data[conn_key] = os.environ[env_key]
        except KeyError:
            pass
    return data
