import random
from zappa.asynchronous import task
from function.task import router
from function.loggers import logging

logger = logging.getLogger(__name__)


@task()
def handler(event, context):
    valid = random.randint(0, 1) == 1
    event['file']['valid'] = valid
    logger.info(event)
    router.handler(event, context)
