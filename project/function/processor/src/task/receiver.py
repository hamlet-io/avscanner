from zappa.asynchronous import task
from function.task import scanner
from function.loggers import logging

logger = logging.getLogger(__name__)


@task
def handler(event, context):
    logger.info(event)
    scanner.handler(event, context)
