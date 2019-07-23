from task import receiver


def handler(event, context):
    receiver.handler(event, context)
