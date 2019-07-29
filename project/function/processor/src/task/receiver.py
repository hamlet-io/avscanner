import datetime
from zappa.asynchronous import task
from loggers import logging
from task import scanner
from s3client import UNPROCESSED_BUCKET


logger = logging.getLogger("RECEIVER")


class InvalidObjectKeyFormat(Exception):
    pass


class InvalidEvent(Exception):
    pass


VALID_S3_EVENT_NAME = 'ObjectCreated:Put'


def recast_event(event):
    try:
        event = event['Records'][0]
        s3 = event['s3']
        key = s3['object']['key']
        bucket = s3['bucket']['name']
        size = s3['object']['size']
        etag = s3['object']['eTag']
        eventName = event['eventName']
        if eventName != VALID_S3_EVENT_NAME:
            raise InvalidEvent(f'Invalid event name:{eventName}')
        if bucket != UNPROCESSED_BUCKET:
            raise InvalidEvent(f'Invalid bucket name:{bucket}')
    except KeyError as e:
        raise InvalidEvent(f'Event missing:{e}') from e
    except IndexError as e:
        raise InvalidEvent('No event in Records') from e
    try:
        year, month, day, user, filename = key.split('/')
    except ValueError as e:
        raise InvalidObjectKeyFormat(f"Invalid key format:{key}") from e
    try:
        year, month, day = int(year), int(month), int(day)
    except ValueError as e:
        raise InvalidObjectKeyFormat(
            f'Invalid date component format:year={year} month={month} day={day}'
        ) from e
    try:
        datetime.datetime(year, month, day).date()
    except ValueError as e:
        raise InvalidObjectKeyFormat(f"Invalid date:{e}") from e
    return dict(
        user=user,
        file=dict(
            name=filename,
            size=size,
            etag=etag,
            bucket=bucket,
            key=key,
            error=None
        ),
        year=year,
        month=month,
        day=day
    )


@task
def handler(event, context):
    try:
        event = recast_event(event)
        logger.info(f'File: {event["file"]["key"]}')
    except InvalidObjectKeyFormat as e:
        # do nothing for now but in future we may move file to another "dir"
        logger.exception(e)
        return True
    except InvalidEvent as e:
        # do nothing because can't handle this event
        logger.exception(e)
        return True
    scanner.handler(event, context)
    return True
