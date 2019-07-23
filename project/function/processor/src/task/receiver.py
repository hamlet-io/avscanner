from zappa.asynchronous import task
from task import scanner
from loggers import logging

logger = logging.getLogger(__name__)


@task
def handler(event, context):
    logger.info(event)
    scanner.handler(event, context)
