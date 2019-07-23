import random
from zappa.asynchronous import task
from task import router, validator
from loggers import logging

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
