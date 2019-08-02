import os
import pytest
from common.dao.filestore import FileStore
from tests.integration.conftest import (
    ARCHIVE_BUCKET,
    QUARANTINE_BUCKET,
    S3_CONNECTION_DATA
)


BUCKET = ARCHIVE_BUCKET
COPY_TARGET_BUCKET = QUARANTINE_BUCKET
FILES = {
    'valid/one.txt': 'one content'.encode(),
    'valid/two.txt': 'two content'.encode()
}

DOWNLOAD_PATH = '/tmp/test'
RECURSIVE_DOWNLOAD_PATH = '/tmp'


@pytest.mark.usefixtures(
    'clear_buckets'
)
def test():
    filestore = FileStore(
        bucket=BUCKET,
        connection_conf=S3_CONNECTION_DATA
    )

    for key, body in FILES.items():
        assert filestore.get(key=key) is None
        filestore.post(key=key, body=body)

        fileobj = filestore.get(key=key)
        content = fileobj['Body'].read()
        assert fileobj is not None

        etag = fileobj['ETag']
        assert filestore.get(key=key, etag='Invalid etag') is None
        etag_fileobj = filestore.get(key=key, etag=etag)
        assert etag_fileobj is not None
        assert etag_fileobj['Body'].read() == content

        try:
            os.remove(DOWNLOAD_PATH)
        except FileNotFoundError:
            pass
        filestore.download(
            path=DOWNLOAD_PATH,
            key=key
        )
        assert os.path.exists(DOWNLOAD_PATH)
        with open(DOWNLOAD_PATH, 'rb') as f:
            assert f.read() == content
        os.remove(DOWNLOAD_PATH)

    # prefix key must end with /
    with pytest.raises(ValueError):
        filestore.download(
            path=RECURSIVE_DOWNLOAD_PATH,
            key='valid',
            recursive=True
        )

    # recursive download path must be dir
    os.mknod(DOWNLOAD_PATH)
    with pytest.raises(ValueError):
        filestore.download(
            path=DOWNLOAD_PATH,
            key='valid',
            recursive=True
        )
    os.remove(DOWNLOAD_PATH)

    filestore.download(
        path=RECURSIVE_DOWNLOAD_PATH,
        key='valid/',
        recursive=True
    )

    files = os.listdir(RECURSIVE_DOWNLOAD_PATH)
    assert len(files) == 2
    for file in files:
        filename = os.path.join(RECURSIVE_DOWNLOAD_PATH, file)
        with open(filename, 'rb') as f:
            assert f.read() == filestore.get(key=f'valid/{file}')['Body'].read()
        os.remove(filename)

    copy_key, move_key = FILES.keys()
    target_copy_key = 'copy.txt'
    target_move_key = 'move.txt'

    copy_content = filestore.get(key=copy_key)['Body'].read()
    move_content = filestore.get(key=move_key)['Body'].read()

    copy_filestore = FileStore(
        bucket=COPY_TARGET_BUCKET,
        connection_conf=S3_CONNECTION_DATA
    )

    filestore.copy(
        key=copy_key,
        target_bucket=COPY_TARGET_BUCKET,
        target_key=target_copy_key
    )

    assert copy_filestore.get(key=target_copy_key)['Body'].read() == copy_content

    filestore.move(
        key=move_key,
        target_key=target_move_key,
        target_bucket=COPY_TARGET_BUCKET
    )

    assert copy_filestore.get(key=target_move_key)['Body'].read() == move_content
    assert filestore.get(key=move_key) is None

    filestore.copy(
        key=copy_key,
        target_key=target_copy_key
    )

    assert filestore.get(key=target_copy_key)['Body'].read() == copy_content

    filestore.move(
        key=target_copy_key,
        target_key=target_move_key
    )

    assert filestore.get(key=target_move_key)['Body'].read() == copy_content
    assert filestore.get(key=target_copy_key) is None
