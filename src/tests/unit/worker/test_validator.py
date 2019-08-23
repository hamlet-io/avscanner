import datetime
import pytz
from processor.worker.validator import ValidatorWorker


def test_get_archive_key_from_event():

    FILENAME = '000000.json'
    USERNAME = 'user'

    def archive_key(
        year,
        month,
        day,
        user=USERNAME,
        filename=FILENAME,
        prefix=''
    ):
        key = f'{year}/{month}/{day}/{user}/{filename}'
        if prefix:
            return '/'.join([prefix, key])
        return key

    def localized_creation_time(
        tz,
        year,
        month,
        day,
        hour=0,
        minute=0
    ):
        return tz.localize(
            datetime.datetime(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute
            )
        )

    def create_event(
        eventTime=None,
        user=USERNAME,
        filename=FILENAME
    ):
        return {
            'eventTime': eventTime.isoformat(),
            's3': {
                'object': {
                    'key': f'private/{user}/submissionInbox/{filename}'
                }
            }
        }

    worker = ValidatorWorker()
    worker.TIMEZONE = pytz.timezone('Australia/Canberra')

    # should not shift date
    event = create_event(
        eventTime=localized_creation_time(worker.TIMEZONE, 2019, 1, 1),
    )
    assert worker.get_archive_key_from_event(event, '') == archive_key(2019, 1, 1)

    # testing key structure
    user = 'testusername'
    filename = 'testfilename'
    event = create_event(
        eventTime=localized_creation_time(worker.TIMEZONE, 2019, 1, 1),
        user=user,
        filename=filename
    )
    assert worker.get_archive_key_from_event(event, 'valid') == archive_key(
        2019, 1, 1,
        user=user,
        filename=filename,
        prefix='valid'
    )

    # should shift date
    event = create_event(
        eventTime=localized_creation_time(pytz.timezone('UTC'), 2019, 1, 1, 15)
    )
    assert worker.get_archive_key_from_event(event, '') == archive_key(2019, 1, 2)

    event = create_event(
        eventTime=localized_creation_time(pytz.timezone('America/Detroit'), 2019, 1, 2, 10)
    )
    assert worker.get_archive_key_from_event(event, '') == archive_key(2019, 1, 3)
