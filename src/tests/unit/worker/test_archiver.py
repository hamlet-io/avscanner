from unittest import mock
import datetime
import pytz
from processor.worker.archiver import ArchiverWorker


def test_archive_date():
    worker = ArchiverWorker()
    worker.TIMEZONE = pytz.timezone('Australia/Canberra')
    # should not shift
    worker.get_current_utc_datetime = mock.MagicMock()
    worker.get_current_utc_datetime.return_value = datetime.datetime(
        year=2019,
        month=2,
        day=1,
        hour=0,
        minute=0,
        tzinfo=datetime.timezone(datetime.timedelta(hours=0))
    )
    date = worker.get_archive_date()
    assert date.year == 2019
    assert date.month == 1

    # testing localized date shift
    worker.get_current_utc_datetime.return_value = datetime.datetime(
        year=2019,
        month=1,
        day=31,
        hour=16,
        minute=0,
        tzinfo=datetime.timezone(datetime.timedelta(hours=0))
    )

    date = worker.get_archive_date()
    assert date.year == 2019
    assert date.month == 1
