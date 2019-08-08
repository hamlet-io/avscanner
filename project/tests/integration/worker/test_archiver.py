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


@pytest.mark.usefixtures(
    'clear_buckets',
    'clear_tmp'
)
@mock.patch('src.worker.archiver.ArchiverWorker.get_current_date')
def test(get_current_date):
    # setting fake current date
    get_current_date.return_value = NOW
    archive_filestore_dao = filestore.Archive(
        conf.get_s3_env_conf()
    )
    worker = ArchiverWorker(
        archive_filestore_dao=archive_filestore_dao
    )
    prefix = '2019/1/'
    assert worker.get_download_files_prefix() == prefix

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

    def unzip_archive(dirname, archive_file):
        os.makedirs(dirname, exist_ok=True)
        subprocess.run(
            ['unzip', archive_file],
            cwd=dirname,
            stdout=subprocess.DEVNULL
        )

    archive_files = create_files(prefix)
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
        key=posixpath.join(
            conf.ARCHIVE_BUCKET_COMPRESSED_DIR,
            prefix,
            ARCHIVE_FILENAME
        ),
        path=COMPRESSED_ARCHIVE_FILE_PATH
    )
    unzip_archive(
        ARCHIVE_DOWNLOAD_DIR,
        COMPRESSED_ARCHIVE_FILE_PATH
    )
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
                assert local_file.read() == archive_files[key]
    assert len(archive_files) == number_of_files
