import logging
import datetime
import json
import posixpath
from unittest import mock
from processor.dao import (
    queue,
    filestore,
    notifications,
    conf
)
from processor.worker.validator import ValidatorWorker
from processor.worker.virus_scanner import VirusScannerWorker
from processor.worker.archiver import ArchiverWorker
from processor.worker.unprocessed_files_auditor import UnprocessedFilesAuditorWorker
from tests.integration.worker.test_archiver import (
    unzip_archive,
    validate_archive_files
)
from tests.integration.worker.test_virus_scanner import (
    event_filename_to_report_key
)
from tests.integration.conftest import (
    event_filename_to_unprocessed_key,
    event_filename_to_archive_key
)

logger = logging.getLogger('COOPERATION')


NOW = datetime.datetime(
    year=2019,
    month=2,
    day=1,
    hour=0,
    minute=0,
    tzinfo=datetime.timezone(datetime.timedelta(hours=0))
)


COMPRESSED_ARCHIVE_FILE_PATH = '/tmp/compressed.zip'
DOWNLOAD_PATH_ARCHIVED_FILES = '/tmp/archive'


@mock.patch('processor.worker.archiver.ArchiverWorker.get_current_utc_datetime', return_value=NOW)
@mock.patch('processor.worker.unprocessed_files_auditor.UnprocessedFilesAuditorWorker.get_utc_now', return_value=NOW)
def test(
    get_utc_now,
    get_current_utc_datetime,
    fill_unprocessed_bucket,
    clear_queues,
    clear_buckets,
    clear_tmp
):
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
    quarantine_filestore_dao = filestore.Quarantine(
        conf.get_s3_env_conf()
    )
    archive_filestore_dao = filestore.Archive(
        conf.get_s3_env_conf()
    )
    unprocessed_filestore_dao = filestore.Unprocessed(
        conf.get_s3_env_conf()
    )
    virus_notifications_dao = notifications.Virus(
        conf.get_sns_env_conf()
    )

    archiver_worker = ArchiverWorker(
        archive_filestore_dao=archive_filestore_dao
    )
    virus_scanner_worker = VirusScannerWorker(
        virus_scanning_queue_dao=virus_scanning_queue_dao,
        validation_queue_dao=validation_queue_dao,
        unprocessed_filestore_dao=unprocessed_filestore_dao,
        quarantine_filestore_dao=quarantine_filestore_dao,
        virus_notifications_dao=virus_notifications_dao
    )
    validator_worker = ValidatorWorker(
        validation_queue_dao=validation_queue_dao,
        unprocessed_filestore_dao=unprocessed_filestore_dao
    )
    unprocessed_files_auditor_worker = UnprocessedFilesAuditorWorker(
        virus_scanning_queue_dao=virus_scanning_queue_dao,
        unprocessed_filestore_dao=unprocessed_filestore_dao
    )

    def post_event_to_virus_scanning_queue(category, filename):
        virus_scanning_queue_dao.post(
            body=json.dumps(unprocessed_bucket_events[category][filename]),
            delay=0
        )

    def process_file(category, filename):
        assert next(virus_scanner_worker)
        if category == 'valid':
            key = event_filename_to_archive_key(filename)
            assert next(validator_worker)
            assert archive_filestore_dao.get(
                key=posixpath.join(
                    conf.ARCHIVE_BUCKET_VALID_DIR,
                    key
                )
            ), key
        elif category == 'invalid':
            key = event_filename_to_archive_key(filename)
            assert next(validator_worker)
            assert archive_filestore_dao.get(
                key=posixpath.join(
                    conf.ARCHIVE_BUCKET_INVALID_DIR,
                    key
                )
            ), key
        elif category == 'virus':
            key = event_filename_to_unprocessed_key(filename)
            assert not next(validator_worker)
            assert quarantine_filestore_dao.get(
                key=key
            ), key
            assert quarantine_filestore_dao.get(
                key=event_filename_to_report_key(filename)
            )

        assert not unprocessed_filestore_dao.get(key=event_filename_to_unprocessed_key(filename))

    logger.info('Testing non JSON file put into unprocessed bucket')
    filename = '2019-1-1-0-user-invalid.json'
    post_event_to_virus_scanning_queue('put', filename)
    process_file('invalid', filename)

    logger.info('Testing valid file put into unprocessed bucket')
    filename = '2019-1-2-0-user-valid.json'
    post_event_to_virus_scanning_queue('put', filename)
    process_file('valid', filename)

    logger.info('Testing virus file put into unprocessed bucket')
    filename = '2019-1-3-1-user-virus.json'
    post_event_to_virus_scanning_queue('put', filename)
    process_file('virus', filename)

    logger.info('Putting couple more valid files to test archiver')
    logger.info('Testing unprocessed files auditor worker. Missing events scenario...')
    # MEMO:
    # Order is essential because list operation which auditor uses sorts everything alphanumerically.
    # At least that's how minio does it, other mock provider may break this part of test.
    # The main idea here is that auditor post events for both of these files.

    get_utc_now.return_value = (NOW + datetime.timedelta(days=30))
    assert unprocessed_files_auditor_worker.get_utc_now() == get_utc_now()
    unprocessed_files_auditor_worker.start()

    filename = '2019-1-3-0-user-valid.json'
    process_file('valid', filename)

    filename = '2019-1-4-0-user-valid.json'
    process_file('valid', filename)

    archive_files = {}
    for key in [
        '2019-1-2-0-user-valid.json',
        '2019-1-3-0-user-valid.json',
        '2019-1-4-0-user-valid.json'
    ]:
        key = posixpath.join(
            conf.ARCHIVE_BUCKET_VALID_DIR,
            event_filename_to_archive_key(key)
        )
        fileobj = archive_filestore_dao.get(key=key)
        assert fileobj
        archive_files[key] = fileobj['Body'].read()

    archiver_worker.start()
    archive_filestore_dao.download(
        key=archiver_worker.archive_filestore_key,
        path=COMPRESSED_ARCHIVE_FILE_PATH
    )
    unzip_archive(DOWNLOAD_PATH_ARCHIVED_FILES, COMPRESSED_ARCHIVE_FILE_PATH)
    validate_archive_files(
        DOWNLOAD_PATH_ARCHIVED_FILES,
        archive_files,
        archiver_worker.download_files_key_prefix
    )
