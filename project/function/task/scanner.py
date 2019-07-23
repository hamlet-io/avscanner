import random
from zappa.asynchronous import task
from function.task import router, validator


@task()
def handler(event, context):
    virus = random.randint(0, 1) == 1
    event['file']['virus'] = virus
    print('scanner', event, context)
    if virus:
        router.handler(event, context)
    else:
        validator.handler(event, context)
