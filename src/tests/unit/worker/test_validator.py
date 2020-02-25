import datetime
import pytz
from processor.worker.validator import ValidatorWorker


def test_get_archive_key_from_event():

    def archive_key(
        year,
        month,
        day,
        user=None,
        submission_time=None,
        prefix=''
    ):
        key = f'{year}/{month}/{day}/{user}/{submission_time.isoformat()}-xxxxxxx.json'
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
        submission_time=None,
        user=None
    ):
        return {
            's3': {
                'object': {
                    'key': f'private/{user}/submissionInbox/{submission_time.isoformat()}-xxxxxxx.json'
                }
            }
        }

    worker = ValidatorWorker()
    worker.TIMEZONE = pytz.timezone('Australia/Canberra')

    # should not shift date
    user = 'username'
    submission_time = localized_creation_time(worker.TIMEZONE, 2019, 1, 1)
    event = create_event(
        user=user,
        submission_time=submission_time,
    )
    assert worker.get_archive_key_from_event(event, '') == archive_key(
        2019, 1, 1,
        user=user,
        submission_time=submission_time
    )

    # testing key structure
    user = 'testusername'
    submission_time = localized_creation_time(worker.TIMEZONE, 2019, 1, 1)
    event = create_event(
        user=user,
        submission_time=submission_time
    )
    assert worker.get_archive_key_from_event(event, 'valid') == archive_key(
        2019, 1, 1,
        user=user,
        submission_time=submission_time,
        prefix='valid'
    )

    # should shift date
    submission_time = localized_creation_time(pytz.timezone('UTC'), 2019, 1, 1, 15)
    event = create_event(
        user=user,
        submission_time=submission_time
    )
    assert worker.get_archive_key_from_event(event, '') == archive_key(
        2019, 1, 2,
        user=user,
        submission_time=submission_time
    )

    submission_time = localized_creation_time(pytz.timezone('America/Detroit'), 2019, 1, 2, 10)
    event = create_event(
        user=user,
        submission_time=submission_time
    )
    assert worker.get_archive_key_from_event(event, '') == archive_key(
        2019, 1, 3,
        user=user,
        submission_time=submission_time
    )
