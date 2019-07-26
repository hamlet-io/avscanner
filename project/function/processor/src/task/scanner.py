import random
import subprocess
from zappa.asynchronous import task
from task import router, validator
from s3client import client, UNPROCESSED_BUCKET
from loggers import logging


logger = logging.getLogger(__name__)

SCANNED_FILE_DOWNLOAD_PATH = '/tmp/scan'


def download_file(event):
    resp = client.get_object(
        Bucket=UNPROCESSED_BUCKET,
        Key=event['file']['key']
    )
    with open(SCANNED_FILE_DOWNLOAD_PATH, 'wb') as f:
        f.write(resp['Body'].read())


def is_virus():
    result = subprocess.run(
        ['clamdscan', SCANNED_FILE_DOWNLOAD_PATH, '--no-summary'],
        capture_output=True,
        encoding='utf-8'
    )
    result = result.stdout.split('\n')[0]
    if result.endswith('OK'):
        return False
    elif result.endswith('FOUND'):
        return True
    # todo: handle unknown clamav response
    raise Exception()


@task()
def handler(event, context):
    download_file(event)
    virus = is_virus()
    event['file']['virus'] = virus
    logger.info(event)
    if virus:
        router.handler(event, context)
    else:
        validator.handler(event, context)
