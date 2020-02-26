import json
import hashlib
import posixpath
import datetime
from unittest import mock
import pytz
import processor.common.event
from processor.worker.unprocessed_files_auditor import UnprocessedFilesAuditorWorker
from processor.dao import (
    queue,
    filestore,
    conf
)
from tests.integration.conftest import ARCHIVE_TIMEZONE

NOW = datetime.datetime(
    year=2019,
    month=1,
    day=2,
    hour=0,
    minute=0,
    tzinfo=datetime.timezone(datetime.timedelta(hours=0))
)


LOCAL_TZ = pytz.timezone(ARCHIVE_TIMEZONE)


def create_filename(
    user=None,
    submission_time=None,
    offset_hours=None
):
    offset_hours = datetime.timedelta(hours=offset_hours) if offset_hours else datetime.timedelta()
    submission_time = (submission_time + offset_hours).isoformat()
    upload_hash = hashlib.md5((user + submission_time).encode()).hexdigest()[:7]
    return posixpath.join(
        'private',
        user,
        'submissionInbox',
        '{}-{}.json'.format(
            submission_time,
            upload_hash
        )
    )


@mock.patch('processor.worker.unprocessed_files_auditor.UnprocessedFilesAuditorWorker.get_utc_now', return_value=NOW)
def test(get_utc_now, clear_queues, clear_buckets, fill_unprocessed_bucket):
    clear_queues()
    clear_buckets()
    NOW_TIMEZONED = NOW.astimezone(pytz.timezone(ARCHIVE_TIMEZONE))
    unprocessed_filestore_dao = filestore.Unprocessed(conf.get_s3_env_conf())
    virus_scanning_queue_dao = queue.VirusScanning(conf.get_sqs_env_conf())
    worker = UnprocessedFilesAuditorWorker(
        unprocessed_filestore_dao=unprocessed_filestore_dao,
        virus_scanning_queue_dao=virus_scanning_queue_dao
    )

    resend_files = {
        create_filename('user-1', NOW_TIMEZONED, -12): b'value-aa',
        create_filename('user-6', NOW_TIMEZONED, -13): b'value-bbb',
        create_filename('user-7', NOW_TIMEZONED, -14): b'value-cccc',
        create_filename('user-4', NOW_TIMEZONED, -15): b'value-eeeee'
    }
    dont_resend_files = {
        create_filename('user-2', NOW_TIMEZONED, -1): b'value',
        create_filename('user-3', NOW_TIMEZONED, -5): b'value',
        create_filename('user-8', NOW_TIMEZONED, -11): b'value'
    }

    files = {**resend_files, **dont_resend_files}

    for key, value in files.items():
        unprocessed_filestore_dao.post(key, value)
    worker.start()
    # testing that queue has at least len(resend_files) messages
    for i in range(len(resend_files)):
        msg = virus_scanning_queue_dao.get(wait_time=1)
        assert msg, i
        virus_scanning_queue_dao.delete(msg)
        # testing event message contents
        event = json.loads(msg.body)['Records'][0]
        key = event['s3']['object']['key']
        etag = event['s3']['object']['eTag']
        size = event['s3']['object']['size']
        bucket = event['s3']['bucket']['name']
        event_time = event['eventTime']
        event_name = event['eventName']

        file = unprocessed_filestore_dao.get(key)
        assert key in resend_files
        assert key not in dont_resend_files
        assert etag == file['ETag']
        assert size == file['ContentLength']
        assert bucket == unprocessed_filestore_dao.bucket.name
        user, submission_time = processor.common.event.parse_unprocessed_file_key(key)
        submission_time = submission_time.astimezone(LOCAL_TZ).isoformat()
        assert (
            event_time
            == submission_time
        )
        assert event_name == "ObjectCreated:Put"
    # testing that queue has no more than len(resend_files) messages
    assert virus_scanning_queue_dao.get(wait_time=1) is None


@mock.patch('processor.worker.unprocessed_files_auditor.UnprocessedFilesAuditorWorker.get_utc_now', return_value=NOW)
def test_exception_cases(get_utc_now, clear_queues, clear_buckets):
    clear_queues()
    clear_buckets()
    unprocessed_filestore_dao = filestore.Unprocessed(conf.get_s3_env_conf())
    virus_scanning_queue_dao = queue.VirusScanning(conf.get_sqs_env_conf())
    worker = UnprocessedFilesAuditorWorker(
        unprocessed_filestore_dao=unprocessed_filestore_dao,
        virus_scanning_queue_dao=virus_scanning_queue_dao
    )

    # test invalid key format should not require resend because NOW is in the past
    key = 'bad-key'
    value = b'bad-key-value'
    unprocessed_filestore_dao.post(key, value)
    worker.start()
    assert virus_scanning_queue_dao.get(wait_time=1) is None

    # test invalid key format should require resend because NOW is in far future
    get_utc_now.return_value = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    worker.start()
    msg = virus_scanning_queue_dao.get(wait_time=1)
    assert msg
    virus_scanning_queue_dao.delete(msg)
    event = json.loads(msg.body)['Records'][0]
    obj_key = event['s3']['object']['key']
    etag = event['s3']['object']['eTag']
    size = event['s3']['object']['size']
    bucket = event['s3']['bucket']['name']
    event_time = event['eventTime']
    event_name = event['eventName']

    file = unprocessed_filestore_dao.get(key)
    assert obj_key == key
    assert etag == file['ETag']
    assert size == file['ContentLength']
    assert bucket == unprocessed_filestore_dao.bucket.name
    # should equal last modification time unlike valid key format which equals submission time parsed from key
    assert event_time == file['LastModified'].astimezone(LOCAL_TZ).isoformat()
    assert event_name == "ObjectCreated:Put"

    # testing FileMovedError
    unprocessed_filestore_dao.get = mock.MagicMock()
    unprocessed_filestore_dao.get.return_value = None
    worker.start()
    assert virus_scanning_queue_dao.get(wait_time=1) is None
