import random
from zappa.asynchronous import task
from function.task import router


@task()
def handler(event, context):
    valid = random.randint(0, 1) == 1
    event['file']['valid'] = valid
    router.handler(event, context)
