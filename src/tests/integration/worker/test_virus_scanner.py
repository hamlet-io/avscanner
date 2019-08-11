import json
from unittest import mock
from processor.dao import (
    queue,
    filestore,
    conf
)
from processor.worker.virus_scanner import VirusScannerWorker


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
    worker = VirusScannerWorker(
        virus_scanning_queue_dao=virus_scanning_queue_dao,
        validation_queue_dao=validation_queue_dao,
        unprocessed_filestore_dao=unprocessed_filestore_dao
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

    # valid file, not a virus
    put = unprocessed_bucket_events['put']

    filename = '2019/1/2/user/valid.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    message = validation_queue_dao.get(wait_time=1)
    assert message
    validation_queue_dao.delete(message)
    assert not quarantine_filestore_dao.get(key=filename)

    # file changed error
    filename = '2019/1/2/user/valid.json'
    unprocessed_filestore_dao.post(
        key=filename,
        body='New body'
    )
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    assert not quarantine_filestore_dao.get(key=filename)

    # test virus
    filename = '2019/1/3/user/virus.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    assert quarantine_filestore_dao.get(key=filename)

    # valid file, not a virus, size too large
    clear_tmp()
    clear_buckets()
    clear_queues()
    unprocessed_bucket_events = fill_unprocessed_bucket()
    put = unprocessed_bucket_events['put']

    WORKER_MAX_FILE_SIZE = worker.MAX_FILE_SIZE

    worker.MAX_FILE_SIZE = -1

    filename = '2019/1/2/user/valid.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    assert quarantine_filestore_dao.get(key=filename)

    # unexpected error test
    worker.MAX_FILE_SIZE = WORKER_MAX_FILE_SIZE
    exception = Exception('Test')
    worker.scan_file = mock.Mock()
    worker.scan_file.side_effect = exception

    filename = '2019/1/3/user/virus.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    assert unprocessed_filestore_dao.get(key=filename)
    assert virus_scanning_queue_dao.get(wait_time=1)
