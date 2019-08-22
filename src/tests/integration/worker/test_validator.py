import json
import posixpath
from unittest import mock
from processor.dao import (
    queue,
    filestore,
    conf
)
from processor.worker.validator import ValidatorWorker
from tests.integration.conftest import (
    event_filename_to_archive_key,
    event_filename_to_unprocessed_key
)


def test(fill_unprocessed_bucket, clear_queues, clear_buckets, clear_tmp):
    clear_tmp()
    clear_queues()
    clear_buckets()
    unprocessed_bucket_events = fill_unprocessed_bucket()
    validation_queue_dao = queue.Validation(
        conf.get_sqs_env_conf()
    )
    unprocessed_filestore_dao = filestore.Unprocessed(
        conf.get_s3_env_conf()
    )
    archive_filestore_dao = filestore.Archive(
        conf.get_s3_env_conf()
    )
    worker = ValidatorWorker(
        validation_queue_dao=validation_queue_dao,
        unprocessed_filestore_dao=unprocessed_filestore_dao
    )
    worker.MESSAGE_VISIBILITY_TIMEOUT = 0
    worker.MESSAGE_WAIT_TIME = 0

    # bad event
    validation_queue_dao.post(
        body=json.dumps({'msg': 'Hello world'}),
        delay=0
    )
    assert next(worker)
    # message must be removed
    assert not validation_queue_dao.get(wait_time=1)

    put = unprocessed_bucket_events['put']

    # testing valid file processing
    filename = '2019-1-2-0-user-valid.json'
    validation_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    # message must be deleted
    assert not validation_queue_dao.get()
    # file moved to archive valid dir
    assert archive_filestore_dao.get(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_VALID_DIR,
            event_filename_to_archive_key(filename)
        )
    )
    # file must be removed from unprocessed filestore
    assert not unprocessed_filestore_dao.get(
        key=event_filename_to_unprocessed_key(filename)
    )

    # testing file changed during processing
    unprocessed_filestore_dao.post(
        body='New body',
        key=event_filename_to_unprocessed_key(filename)
    )
    # deleting file from archive to check that it wasn't added
    archive_filestore_dao.delete(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_VALID_DIR,
            event_filename_to_archive_key(filename)
        )
    )
    validation_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    # message must be deleted because it's an ok situation
    assert not validation_queue_dao.get()
    # but file must not be moved to archive
    assert not archive_filestore_dao.get(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_VALID_DIR,
            event_filename_to_archive_key(filename)
        )
    )
    assert unprocessed_filestore_dao.get(
        key=event_filename_to_unprocessed_key(filename)
    )

    # testing invalid file
    filename = '2019-1-1-0-user-invalid.json'
    validation_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    # message removed
    assert not validation_queue_dao.get()
    # file must be moved to invalid archive dir
    assert archive_filestore_dao.get(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_INVALID_DIR,
            event_filename_to_archive_key(filename)
        )
    )
    # file must be removed from unprocessed filestore
    assert not unprocessed_filestore_dao.get(
        key=event_filename_to_unprocessed_key(filename)
    )

    # test unexpected error, message must remain in the queue
    worker.download_json_file = mock.MagicMock()
    worker.download_json_file.side_effect = Exception()
    validation_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert validation_queue_dao.get(wait_time=1)
