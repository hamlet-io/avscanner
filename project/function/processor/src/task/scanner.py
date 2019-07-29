import subprocess
from zappa.asynchronous import task
from task import router, validator
from s3client import FileChangedError, get_unprocessed_file_object
from loggers import logging


logger = logging.getLogger(__name__)

SCANNED_FILE_DOWNLOAD_PATH = '/tmp/scan'
MAX_FILE_SIZE = 1024 * 1024 * 400  # 400 MB


class UnknownClamavResult(Exception):
    pass


def is_file_too_large(event):
    return event['file']['size'] > MAX_FILE_SIZE


def download_file(event):
    resp = get_unprocessed_file_object(event)
    with open(SCANNED_FILE_DOWNLOAD_PATH, 'wb') as f:
        f.write(resp['Body'].read())


def is_virus():
    result = subprocess.run(
        ['clamdscan', SCANNED_FILE_DOWNLOAD_PATH, '--no-summary'],
        capture_output=True,
        encoding='utf8'
    )
    result = result.stdout.split('\n')[0]
    if result.endswith('OK'):
        return False
    elif result.endswith('FOUND'):
        return True
    raise UnknownClamavResult(result.stdout)


@task()
def handler(event, context):
    if is_file_too_large(event):
        event['file']['virus'] = True
        router.handler(event, context)
        return True
    try:
        download_file(event)
    except FileChangedError:
        # Stop if file changed
        return True
    try:
        virus = is_virus()
    except UnknownClamavResult as e:
        logger.error('Unknown clamav result. Moving file to quarantine.')
        logger.exception(e)
        event['file']['virus'] = True
        router.handler(event, context)
        return True
    event['file']['virus'] = virus
    logger.info(event)
    if virus:
        router.handler(event, context)
    else:
        validator.handler(event, context)
