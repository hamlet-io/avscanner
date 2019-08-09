import logging
import json
import posixpath
import pytest
from processor.dao import (
    queue,
    filestore,
    conf
)
from processor.worker.validator import ValidatorWorker
from processor.worker.virus_scanner import VirusScannerWorker


logger = logging.getLogger('COOPERATION')


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
    quarantine_filestore_dao = filestore.Quarantine(
        conf.get_s3_env_conf()
    )
    archive_filestore_dao = filestore.Archive(
        conf.get_s3_env_conf()
    )
    unprocessed_filestore_dao = filestore.Unprocessed(
        conf.get_s3_env_conf()
    )
    virus_scanner_worker = VirusScannerWorker(
        virus_scanning_queue_dao=virus_scanning_queue_dao,
        validation_queue_dao=validation_queue_dao,
        unprocessed_filestore_dao=unprocessed_filestore_dao
    )
    validator_worker = ValidatorWorker(
        validation_queue_dao=validation_queue_dao,
        unprocessed_filestore_dao=unprocessed_filestore_dao
    )
    virus_scanner_worker.MESSAGE_VISIBILITY_TIMEOUT = 60
    virus_scanner_worker.MESSAGE_WAIT_TIME = 1
    validator_worker.MESSAGE_VISIBILITY_TIMEOUT = 60
    validator_worker.MESSAGE_WAIT_TIME = 1

    def post_event_to_virus_scanning_queue(category, filename):
        virus_scanning_queue_dao.post(
            body=json.dumps(unprocessed_bucket_events[category][filename]),
            delay=0
        )

    logger.info('Testing non JSON file put into unprocessed bucket')
    filename = '2019/1/1/user/invalid.json'
    post_event_to_virus_scanning_queue('put', filename)
    assert next(virus_scanner_worker)
    assert next(validator_worker)
    assert archive_filestore_dao.get(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_INVALID_DIR,
            filename
        )
    )
    assert not unprocessed_filestore_dao.get(
        key=filename
    )

    logger.info('Testing valid file put into unprocessed bucket')
    filename = '2019/1/2/user/valid.json'
    post_event_to_virus_scanning_queue('put', filename)
    assert next(virus_scanner_worker)
    assert next(validator_worker)
    assert archive_filestore_dao.get(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_VALID_DIR,
            filename
        )
    )
    assert not unprocessed_filestore_dao.get(
        key=filename
    )

    logger.info('Testing virus file put into unprocessed bucket')
    filename = '2019/1/3/user/virus.json'
    post_event_to_virus_scanning_queue('put', filename)
    assert next(virus_scanner_worker)
    assert not next(validator_worker)
    assert quarantine_filestore_dao.get(
        key=filename
    )
    assert not unprocessed_filestore_dao.get(
        key=filename
    )
