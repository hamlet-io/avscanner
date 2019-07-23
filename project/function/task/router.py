from zappa.asynchronous import task


@task()
def handler(event, context):
    if event['file']['virus']:
        print('Router', 'Saved to quarantine')
    elif not event['file']['valid']:
        print('Router', 'Saved to invalid')
    else:
        print('Router', 'Saved to valid')
    print('Router', 'Removed file from unprocessed bucket')
    return True
