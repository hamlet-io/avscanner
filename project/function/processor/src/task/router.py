from zappa.asynchronous import task
from loggers import logging
from s3client import client, PROCESSED_BUCKET, UNPROCESSED_BUCKET


logger = logging.getLogger(__name__)

QUARANTINE_DIR = 'quarantine'
VALID_DIR = 'valid'
INVALID_DIR = 'invalid'


def put_object(directory, event):
    # todo add exception handling
    key = "{}/{}/{}/{}/{}/{}".format(
        directory,
        event['year'],
        event['month'],
        event['day'],
        event['user'],
        event['file']['name']
    )
    response = client.get_object(
        Bucket=UNPROCESSED_BUCKET,
        Key=event['file']['key']
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
