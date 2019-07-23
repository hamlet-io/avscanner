from zappa.asynchronous import task
from function.task import scanner


@task
def handler(event, context):
    print('receiver', event)
    scanner.handler(event, context)
