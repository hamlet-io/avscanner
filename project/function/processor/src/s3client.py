import os
from http import HTTPStatus
import boto3
from botocore.exceptions import ClientError

CONFIG = dict()

CONFIG['aws_access_key_id'] = os.environ['AWS_S3_ACCESS_KEY_ID']
CONFIG['aws_secret_access_key'] = os.environ['AWS_S3_SECRET_ACCESS_KEY']
CONFIG['endpoint_url'] = os.environ['AWS_S3_ENDPOINT_URL']


UNPROCESSED_BUCKET = os.environ['UNPROCESSED_BUCKET_NAME']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET_NAME']

client = boto3.client(
    's3',
    **CONFIG
)


class FileChangedError(Exception):
    pass


def get_unprocessed_file_object(event):
    try:
        response = client.get_object(
            Bucket=UNPROCESSED_BUCKET,
            Key=event['file']['key'],
            IfMatch=event['file']['etag']
        )
        return response
    except ClientError as e:
        status_code = e.response['ResponseMetadata']['HTTPStatusCode']
        if status_code == HTTPStatus.PRECONDITION_FAILED:
            raise FileChangedError() from e
        raise
