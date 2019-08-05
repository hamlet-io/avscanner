import os
import pytest
from common.dao.filestore import FileStore, FileChangedError
from tests.integration.conftest import (
    ARCHIVE_BUCKET,
    QUARANTINE_BUCKET,
    S3_CONNECTION_DATA
)


BUCKET = ARCHIVE_BUCKET
COPY_TARGET_BUCKET = QUARANTINE_BUCKET
FILES = {
    'valid/one.txt': 'one content'.encode(),
    'valid/two.txt': 'two content'.encode(),
    'valid/three.txt': 'three content'.encode()
}

DOWNLOAD_PATH = '/tmp/test'
RECURSIVE_DOWNLOAD_PATH = '/tmp'


@pytest.mark.usefixtures(
    'clear_buckets',
    'clear_tmp'
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
            key=key,
            etag=etag
        )
        assert os.path.exists(DOWNLOAD_PATH)
        with open(DOWNLOAD_PATH, 'rb') as f:
            assert f.read() == content
        os.remove(DOWNLOAD_PATH)
        with pytest.raises(FileChangedError):
            filestore.download(
                path=DOWNLOAD_PATH,
                key=key,
                etag='Invalid etag'
            )
        assert not os.path.exists(DOWNLOAD_PATH)

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
    assert len(files) == len(FILES)
    for file in files:
        filename = os.path.join(RECURSIVE_DOWNLOAD_PATH, file)
        with open(filename, 'rb') as f:
            assert f.read() == filestore.get(key=f'valid/{file}')['Body'].read()
        os.remove(filename)

    copy_key, move_key, *rest = FILES.keys()
    target_copy_key = 'copy.txt'
    target_move_key = 'move.txt'

    copy_obj = filestore.get(key=copy_key)
    copy_content = copy_obj['Body'].read()
    copy_etag = copy_obj['ETag']
    move_obj = filestore.get(key=move_key)
    move_content = move_obj['Body'].read()
    move_etag = move_obj['ETag']

    copy_filestore = FileStore(
        bucket=COPY_TARGET_BUCKET,
        connection_conf=S3_CONNECTION_DATA
    )

    invalid_etag = 'Invalid etag'

    def test_copy(etag, bucket=COPY_TARGET_BUCKET):
        filestore.copy(
            key=copy_key,
            target_bucket=COPY_TARGET_BUCKET,
            target_key=target_copy_key,
            etag=etag
        )
        assert copy_filestore.get(key=target_copy_key)['Body'].read() == copy_content
        assert copy_filestore.delete(key=target_copy_key)
        assert not copy_filestore.get(key=target_copy_key)

    for etag in [None, copy_etag]:
        test_copy(etag)
    with pytest.raises(FileChangedError):
        test_copy(invalid_etag)

    def test_move(etag):
        filestore.move(
            key=move_key,
            target_key=target_move_key,
            target_bucket=COPY_TARGET_BUCKET,
            etag=etag
        )

        assert copy_filestore.get(key=target_move_key)['Body'].read() == move_content
        assert filestore.get(key=move_key) is None

    with pytest.raises(FileChangedError):
        test_move(invalid_etag)

    test_move(move_etag)

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


@pytest.mark.usefixtures(
    'clear_buckets'
)
def test_bulk_delete():
    filestore = FileStore(
        bucket=BUCKET,
        connection_conf=S3_CONNECTION_DATA
    )
    for prefix in ['/', 'valid', 'valid/']:
        for key, body in FILES.items():
            filestore.post(key=key, body=body)
        assert filestore.delete(recursive=True, key=prefix) == len(FILES)
