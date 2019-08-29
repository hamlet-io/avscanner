import json
import posixpath
from processor.dao import (
    queue,
    filestore,
    notifications,
    conf
)
from processor.worker.virus_scanner import VirusScannerWorker
from tests.integration.conftest import (
    event_filename_to_unprocessed_key
)


def event_filename_to_report_key(filename):
    key = event_filename_to_unprocessed_key(filename)
    report_filename = posixpath.splitext(posixpath.basename(key))[0] + '.report.json'
    return posixpath.join(
        posixpath.dirname(key),
        report_filename
    )


def test(fill_unprocessed_bucket, clear_queues, clear_buckets, clear_tmp):
    clear_tmp()
    clear_queues()
    clear_buckets()

    unprocessed_bucket_events = fill_unprocessed_bucket()
    virus_scanning_queue_dao = queue.VirusScanning(
        conf.get_sqs_env_conf()
    )
    validation_queue_dao = queue.Validation(
        conf.get_sqs_env_conf()
    )
    unprocessed_filestore_dao = filestore.Unprocessed(
        conf.get_s3_env_conf()
    )
    quarantine_filestore_dao = filestore.Quarantine(
        conf.get_s3_env_conf()
    )
    virus_notifications_dao = notifications.Virus(
        conf.get_sns_env_conf()
    )
    worker = VirusScannerWorker(
        virus_scanning_queue_dao=virus_scanning_queue_dao,
        validation_queue_dao=validation_queue_dao,
        unprocessed_filestore_dao=unprocessed_filestore_dao,
        quarantine_filestore_dao=quarantine_filestore_dao,
        virus_notifications_dao=virus_notifications_dao
    )
    worker.MESSAGE_VISIBILITY_TIMEOUT = 0
    worker.MESSAGE_WAIT_TIME = 0
    # bad event
    virus_scanning_queue_dao.post(
        body=json.dumps({'msg': 'Hello world'}),
        delay=0
    )
    assert next(worker)
    # message must be removed
    assert not validation_queue_dao.get(wait_time=1)

    put = unprocessed_bucket_events['put']
    # unexpected error / scanner error, message must remain
    worker.VIRUS_SCAN_COMMAND = [
        'clamdscan',
        'badfilenameshouldnotexist',
        '--no-summary'
    ]
    filename = '2019-1-2-0-user-valid.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    message = virus_scanning_queue_dao.get(wait_time=1)
    assert message
    virus_scanning_queue_dao.delete(message=message)
    worker.VIRUS_SCAN_COMMAND = VirusScannerWorker.VIRUS_SCAN_COMMAND
    assert not quarantine_filestore_dao.get(
        key=event_filename_to_unprocessed_key(filename)
    )

    # valid file, not a virus
    filename = '2019-1-2-0-user-valid.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    message = validation_queue_dao.get(wait_time=1)
    assert message
    validation_queue_dao.delete(message)
    assert not quarantine_filestore_dao.get(
        key=event_filename_to_unprocessed_key(filename)
    )

    # file changed error
    filename = '2019-1-2-0-user-valid.json'
    unprocessed_filestore_dao.post(
        key=event_filename_to_unprocessed_key(filename),
        body='New body'
    )
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    assert not quarantine_filestore_dao.get(
        key=event_filename_to_unprocessed_key(filename)
    )

    # test virus
    filename = '2019-1-3-1-user-virus.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    assert quarantine_filestore_dao.get(
        key=event_filename_to_unprocessed_key(filename)
    )
    assert quarantine_filestore_dao.get(
        key=event_filename_to_report_key(filename)
    )

    # valid file, not a virus, size too large
    unprocessed_bucket_events = fill_unprocessed_bucket()
    put = unprocessed_bucket_events['put']

    worker.MAX_FILE_SIZE = -1

    filename = '2019-1-2-0-user-valid.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    assert quarantine_filestore_dao.get(
        key=event_filename_to_unprocessed_key(filename)
    )
    assert quarantine_filestore_dao.get(
        key=event_filename_to_report_key(filename)
    )
