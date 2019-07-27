import os
from zappa.asynchronous import task
from loggers import logging
from s3client import (
    client,
    PROCESSED_BUCKET,
    UNPROCESSED_BUCKET,
    get_unprocessed_file_object,
    FileChangedError
)


logger = logging.getLogger(__name__)

QUARANTINE_DIR = os.environ['QUARANTINE_DIR']
VALID_DIR = os.environ['VALID_DIR']
INVALID_DIR = os.environ['INVALID_DIR']


def put_object(directory, event):
    # todo add exception handling
    try:
        response = get_unprocessed_file_object(event)
    except FileChangedError:
        # Stop if file changed
        return True
    key = "{}/{}/{}/{}/{}/{}".format(
        directory,
        event['year'],
        event['month'],
        event['day'],
        event['user'],
        event['file']['name']
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
        logger.warn(f'Virus found and placed to quarantine. Filename:{key}')
    return True


@task()
def handler(event, context):
    if event['file']['virus']:
        put_object(QUARANTINE_DIR, event)
    elif not event['file']['valid']:
        put_object(INVALID_DIR, event)
    else:
        put_object(VALID_DIR, event)
    return True
