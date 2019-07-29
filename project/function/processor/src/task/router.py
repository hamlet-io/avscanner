import os
import posixpath
from zappa.asynchronous import task
from loggers import logging
from s3client import (
    client,
    PROCESSED_BUCKET,
    UNPROCESSED_BUCKET,
    get_unprocessed_file_object,
    FileChangedError
)


logger = logging.getLogger("ROUTER")

QUARANTINE_DIR = os.environ['QUARANTINE_DIR']
VALID_DIR = os.environ['VALID_DIR']
INVALID_DIR = os.environ['INVALID_DIR']
ERROR_DIR = os.environ['ERROR_DIR']


def put_object(directory, event):
    # todo add boto3 exception handling
    try:
        response = get_unprocessed_file_object(event)
    except FileChangedError:
        logger.warn('File changed during processing. Stopping.')
        return True
    key = posixpath.join(
        str(directory),
        str(event['year']),
        str(event['month']),
        str(event['day']),
        str(event['user']),
        str(event['file']['name'])
    )
    response = client.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=key,
        Body=response['Body'].read()
    )
    client.delete_object(
        Bucket=UNPROCESSED_BUCKET,
        Key=event['file']['key']
    )
    if directory == QUARANTINE_DIR:
        logger.warn(f'Virus isolated:{key}')
    else:
        logger.info(f'File saved: {key}')
    return True


@task()
def handler(event, context):
    if event['file']['error']:
        put_object(posixpath.join(ERROR_DIR, event['file']['error']), event)
    elif event['file']['virus']:
        put_object(QUARANTINE_DIR, event)
    elif not event['file']['valid']:
        put_object(INVALID_DIR, event)
    else:
        put_object(VALID_DIR, event)
    return True
