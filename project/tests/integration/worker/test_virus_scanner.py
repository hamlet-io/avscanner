import json
import pytest
from src.dao import (
    queue,
    filestore,
    conf
)
from src.worker.virus_scanner import VirusScannerWorker


@pytest.mark.usefixtures(
    'clear_tmp',
    'clear_buckets',
    'clear_queues',
    'fill_unprocessed_bucket'
)
def test(unprocessed_bucket_events):
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
    # bad event
    virus_scanning_queue_dao.post(
        body=json.dumps({'msg': 'Hello world'}),
        delay=0
    )
    message = virus_scanning_queue_dao.get(visibility_timeout=0)
    assert next(worker)
    assert not validation_queue_dao.get(wait_time=1)
    virus_scanning_queue_dao.delete(message)

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

    # invalid file, not a virus
    filename = '2019/1/1/user/invalid.json'
    virus_scanning_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    message = validation_queue_dao.get(wait_time=1)
    assert message
    validation_queue_dao.delete(message)
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
