import os
import uuid
import subprocess
import posixpath
import datetime
from unittest import mock
import pytest
from src.dao import (
    filestore,
    conf
)
from src.worker.archiver import (
    ArchiverWorker,
    ARCHIVE_FILENAME,
    COMPRESSED_ARCHIVE_FILE_PATH,
    ARCHIVE_DOWNLOAD_DIR
)


NOW = datetime.datetime(
    year=2019,
    month=2,
    day=1
).date()

PREFIX = '2019/1/'


def unzip_archive(dirname, archive_file):
    os.makedirs(dirname, exist_ok=True)
    subprocess.run(
        ['unzip', archive_file],
        cwd=dirname,
        stdout=subprocess.DEVNULL
    )


def create_files(prefix):
    files = dict()
    index = 0
    for user in ['a', 'b', 'c']:
        for day in range(30):
            index += 1
            filename = f'file-{index}'
            key = f'{prefix}{day}/{user}/{filename}'
            files[key] = str(uuid.uuid4()).encode('utf8')
    return files


def validate_archive_files(unzipped_dir, files, prefix):
    number_of_files = 0
    for dirpath, dirnames, filenames in os.walk(ARCHIVE_DOWNLOAD_DIR):
        for filename in filenames:
            key = posixpath.join(
                prefix,
                posixpath.relpath(
                    posixpath.join(dirpath, filename),
                    ARCHIVE_DOWNLOAD_DIR
                )
            )
            number_of_files += 1
            with open(os.path.join(dirpath, filename), 'rb') as local_file:
                assert local_file.read() == files[key]
    assert len(files) == number_of_files


@pytest.mark.usefixtures(
    'clear_buckets',
    'clear_tmp'
)
@mock.patch('src.worker.archiver.ArchiverWorker.get_current_date', return_value=NOW)
def test(get_current_date):
    archive_filestore_dao = filestore.Archive(
        conf.get_s3_env_conf()
    )
    worker = ArchiverWorker(
        archive_filestore_dao=archive_filestore_dao
    )
    assert worker.get_download_files_prefix() == PREFIX

    archive_files = create_files(PREFIX)
    non_archive_files = create_files('2019/2/')
    files = {**archive_files, **non_archive_files}

    for key, body in files.items():
        archive_filestore_dao.post(
            key=key,
            body=body
        )
    worker.start()
    # check that local files removed
    assert not os.path.exists(ARCHIVE_DOWNLOAD_DIR)
    assert not os.path.exists(COMPRESSED_ARCHIVE_FILE_PATH)
    # check that archived files removed but non archive files remain unchanged
    for key in archive_files:
        assert not archive_filestore_dao.get(key=key)
    for key in non_archive_files:
        f = archive_filestore_dao.get(key=key)
        assert f
        assert f['Body'].read() == non_archive_files[key]

    # check the composition of the archive
    assert archive_filestore_dao.download(
        key=worker.get_archive_filestore_key(PREFIX),
        path=COMPRESSED_ARCHIVE_FILE_PATH
    )
    unzip_archive(
        ARCHIVE_DOWNLOAD_DIR,
        COMPRESSED_ARCHIVE_FILE_PATH
    )
    validate_archive_files(ARCHIVE_DOWNLOAD_DIR, archive_files, PREFIX)


@pytest.mark.usefixtures(
    'clear_tmp',
    'clear_buckets'
)
def test_no_files_to_archive():
    archive_filestore_dao = filestore.Archive(
        conf.get_s3_env_conf()
    )
    worker = ArchiverWorker(
        archive_filestore_dao=archive_filestore_dao
    )
    worker.start()


@pytest.mark.usefixtures(
    'clear_tmp',
    'clear_buckets'
)
@mock.patch('src.worker.archiver.ArchiverWorker.get_current_date', return_value=NOW)
def test_archive_exists(get_current_date):
    archive_filestore_dao = filestore.Archive(
        conf.get_s3_env_conf()
    )
    worker = ArchiverWorker(
        archive_filestore_dao=archive_filestore_dao
    )

    def add_files_to_filestore():
        files = create_files(PREFIX)
        for key, body in files.items():
            archive_filestore_dao.post(
                key=key,
                body=body
            )
    add_files_to_filestore()
    # creating archive
    worker.start()
    archive_fileobj_key = worker.get_archive_filestore_key(PREFIX)
    archive_fileobj = archive_filestore_dao.get(key=archive_fileobj_key)
    assert archive_fileobj
    # created archive should not change
    worker.start()
    add_files_to_filestore()
    assert archive_filestore_dao.get(
        key=archive_fileobj_key,
        etag=archive_fileobj['ETag']
    )
