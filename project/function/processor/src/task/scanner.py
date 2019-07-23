import random
from zappa.asynchronous import task
from function.task import router, validator
from function.loggers import logging

logger = logging.getLogger(__name__)


@task()
def handler(event, context):
    virus = random.randint(0, 1) == 1
    event['file']['virus'] = virus
    logger.info(event)
    if virus:
        router.handler(event, context)
    else:
        validator.handler(event, context)
