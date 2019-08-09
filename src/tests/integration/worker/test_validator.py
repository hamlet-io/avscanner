import json
import posixpath
import pytest
from processor.dao import (
    queue,
    filestore,
    conf
)
from processor.worker.validator import ValidatorWorker


@pytest.mark.usefixtures(
    'clear_buckets',
    'clear_queues',
    'fill_unprocessed_bucket'
)
def test(unprocessed_bucket_events):
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

    filename = '2019/1/2/user/valid.json'
    validation_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get()
    assert archive_filestore_dao.get(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_VALID_DIR,
            filename
        )
    )

    # testing file changed during processing
    unprocessed_filestore_dao.post(
        body='New body',
        key=filename
    )
    # deleting file from archive to check that it wasn't added
    archive_filestore_dao.delete(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_VALID_DIR,
            filename
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
            filename
        )
    )

    filename = '2019/1/1/user/invalid.json'
    validation_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get()
    assert archive_filestore_dao.get(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_INVALID_DIR,
            filename
        )
    )

    filename = '2019/1/4/user/invalid.schema.json'
    validation_queue_dao.post(
        body=json.dumps(put[filename]),
        delay=0
    )
    assert next(worker)
    assert not validation_queue_dao.get()
    assert archive_filestore_dao.get(
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_INVALID_DIR,
            filename
        )
    )
