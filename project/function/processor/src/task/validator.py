import random
from zappa.asynchronous import task
from task import router
from loggers import logging

logger = logging.getLogger(__name__)


@task()
def handler(event, context):
    valid = random.randint(0, 1) == 1
    event['file']['valid'] = valid
    logger.info(event)
    router.handler(event, context)
