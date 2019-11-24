import os
import pytest
from common.dao.filestore import FileStore, FileChangedError
from tests.integration.conftest import (
    ARCHIVE_BUCKET,
    UNPROCESSED_BUCKET,
    S3_CONNECTION_DATA
)


BUCKET = UNPROCESSED_BUCKET
COPY_TARGET_BUCKET = ARCHIVE_BUCKET
FILES = {
    'valid/1/one.txt': 'one content'.encode(),
    'valid/2/two.txt': 'two content'.encode(),
    'valid/3/three.txt': 'three content'.encode()
}

DOWNLOAD_PATH = '/tmp/test'
RECURSIVE_DOWNLOAD_PATH = '/tmp'


def test(clear_tmp, clear_buckets):
    clear_tmp()
    clear_buckets()
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
        with pytest.raises(FileChangedError):
            assert filestore.delete(key=key, etag='Invalid etag')
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

    files = []
    for dirpath, dirnames, filenames in os.walk(RECURSIVE_DOWNLOAD_PATH):
        for filename in filenames:
            files.append(os.path.join(dirpath, filename))
    assert len(files) == len(FILES)
    for filename in files:
        with open(filename, 'rb') as f:
            key = f'valid/{os.path.relpath(filename, RECURSIVE_DOWNLOAD_PATH)}'
            assert f.read() == filestore.get(key=key)['Body'].read()
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


def test_bulk_delete(clear_buckets):
    clear_buckets()
    filestore = FileStore(
        bucket=BUCKET,
        connection_conf=S3_CONNECTION_DATA
    )
    for prefix in ['/', 'valid', 'valid/']:
        for key, body in FILES.items():
            filestore.post(key=key, body=body)
        assert filestore.delete(recursive=True, key=prefix) == len(FILES)


def test_list(clear_buckets):
    clear_buckets()
    filestore = FileStore(
        bucket=BUCKET,
        connection_conf=S3_CONNECTION_DATA
    )
    files = {
        'a/b/1': b'value-ab1',
        'a/b/2': b'value-ab2',
        'b/a/1': b'value-ba1',
        'b/a/2': b'value-ba2',
        'b/a/3': b'value-ba3'
    }
    for prefix, count in {'a/b': 2, 'b/a': 3}.items():
        for key, value in files.items():
            filestore.post(key=key, body=value)
        listed_count = 0
        for key in filestore.list(key=prefix):
            listed_count += 1
            assert key in files
            assert key.startswith(prefix)
            assert filestore.get(key)['Body'].read() == files[key]
        assert count == listed_count
    listed_count = 0
    for key in filestore.list():
        listed_count += 1
        assert key in files
        assert filestore.get(key)['Body'].read() == files[key]
    assert listed_count == len(files)
