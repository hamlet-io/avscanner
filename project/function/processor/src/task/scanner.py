import subprocess
from zappa.asynchronous import task
from task import router, validator
from s3client import FileChangedError, get_unprocessed_file_object
from loggers import logging


logger = logging.getLogger("SCANNER")

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
        ['clamdscan', SCANNED_FILE_DOWNLOAD_PATH],
        capture_output=True,
        encoding='utf8'
    )
    file_status = result.stdout.split('\n')[0]
    if file_status.endswith('OK'):
        return False
    elif file_status.endswith('FOUND'):
        return True
    raise UnknownClamavResult(result.stdout)


@task()
def handler(event, context):
    if is_file_too_large(event):
        event['file']['virus'] = True
        logger.warn('The file is too large. Cannot check on viruses. Treated as a virus.')
        router.handler(event, context)
        return True
    try:
        download_file(event)
    except FileChangedError:
        logger.warn('File changed during processing. Stopping.')
        return True
    try:
        virus = is_virus()
        event['file']['virus'] = virus
        logger.info(f'File:{event["file"]["key"]} is{"" if virus else " not"} a virus')
        if virus:
            router.handler(event, context)
        else:
            validator.handler(event, context)
        return True
    except UnknownClamavResult as e:
        logger.exception(e)
        event['file']['error'] = UnknownClamavResult.__name__
        router.handler(event, context)
        return True
