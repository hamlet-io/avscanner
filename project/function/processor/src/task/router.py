from zappa.asynchronous import task
from loggers import logging

logger = logging.getLogger(__name__)


@task()
def handler(event, context):
    if event['file']['virus']:
        logger.info('Saved to quarantine')
    elif not event['file']['valid']:
        logger.info('Saved to invalid')
    else:
        logger.info('Saved to valid')
    logger.info('Removed file from unprocessed bucket')
    return True
