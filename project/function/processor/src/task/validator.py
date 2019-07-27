import json
from zappa.asynchronous import task
from s3client import get_unprocessed_file_object, FileChangedError
from task import router
from loggers import logging


logger = logging.getLogger(__name__)


def is_valid(data):
    try:
        data = data.decode('utf8')
    except ValueError:
        return False
    try:
        data = json.loads(data)
    except ValueError:
        return False
    return True


@task()
def handler(event, context):
    try:
        file_object = get_unprocessed_file_object(event)
    except FileChangedError:
        return True
    event['file']['valid'] = is_valid(file_object['Body'].read())
    logger.info(event)
    router.handler(event, context)
