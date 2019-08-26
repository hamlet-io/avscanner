import os
import time
import tempfile
import subprocess
import datetime
import pytz
from common import loggers
from dao import (
    conf,
    filestore
)

default_logger = loggers.logging.getLogger('ARCHIVER_WORKER')

# paths relative to tmp dir generated on start
DOWNLOAD_PATH_ARCHIVED_FILES = 'archive'
# must have zip extension, otherwise zip will add extension to filename and code will fail
COMPRESSED_ARCHIVE_FILE_PATH = 'compressed.zip'
ARCHIVE_FILENAME = 'archive.zip'


class NoFilesToArchive(Exception):
    pass


class ArchiveExists(Exception):
    pass


class ArchiverWorker:

    TIMEZONE = pytz.timezone(os.environ['ARCHIVE_TIMEZONE'])

    def __init__(
        self,
        archive_filestore_dao=None,
        logger=None
    ):
        self.archive_filestore_dao = archive_filestore_dao
        self.logger = logger if logger else default_logger

    def get_size(self, filename):
        result = subprocess.run(
            ['du', '-s', filename],
            capture_output=True,
            encoding='utf8'
        )
        size = int(result.stdout.split('\t')[0])
        return size / 1024

    def create_dirs(self, tmpdir):
        self.compressed_archive_file_path = os.path.join(tmpdir, COMPRESSED_ARCHIVE_FILE_PATH)
        self.archive_files_download_dir = os.path.join(tmpdir, DOWNLOAD_PATH_ARCHIVED_FILES)
        os.makedirs(os.path.dirname(self.compressed_archive_file_path), exist_ok=True)
        os.makedirs(self.archive_files_download_dir, exist_ok=True)
        self.logger.info('Archive files download dir %s', self.archive_files_download_dir)
        self.logger.info('Compressed archive path %s', self.compressed_archive_file_path)

    # for easy mocking
    def get_current_utc_datetime(self):
        return datetime.datetime.utcnow()

    # date must be localized to be in synch with validator worker
    def get_localized_date(self):
        return self.get_current_utc_datetime().astimezone(self.TIMEZONE).date()

    # this will return last day of previous month
    # meaning that created archive will contain files uploaded last month
    def get_archive_date(self):
        date = self.get_localized_date()
        date.replace(day=1)
        date -= datetime.timedelta(days=1)
        return date

    def create_keys(self):
        date_prefix = self.get_archive_date().strftime('%Y/%-m')
        self.download_files_key_prefix = "{}/{}/".format(
            conf.ARCHIVE_BUCKET_VALID_DIR,
            date_prefix
        )
        self.archive_filestore_key = "{}/{}/{}".format(
            conf.ARCHIVE_BUCKET_COMPRESSED_DIR,
            date_prefix,
            ARCHIVE_FILENAME
        )

    def check_archive_not_exists(self):
        self.logger.info('Checking that archive file %s does not exist...', self.archive_filestore_key)
        if self.archive_filestore_dao.get(key=self.archive_filestore_key) is not None:
            raise ArchiveExists()
        self.logger.info('Archive file %s not found. Continuing...', self.archive_filestore_key)

    def download_files(self):
        self.logger.info(
            'Downloading valid files from %s to %s',
            self.download_files_key_prefix,
            self.archive_files_download_dir
        )
        number_of_files = self.archive_filestore_dao.download(
            recursive=True,
            key=self.download_files_key_prefix,
            path=self.archive_files_download_dir
        )
        if number_of_files == 0:
            raise NoFilesToArchive()
        size = self.get_size(self.archive_files_download_dir)
        self.logger.info(
            'Downloaded %i files from %s. Size %f MB',
            number_of_files,
            self.download_files_key_prefix,
            size
        )

    def zip_files(self):
        self.logger.info('Starting compression...')
        uncompressed_size = self.get_size(self.archive_files_download_dir)
        start_time = time.time()
        subprocess.run(
            ['zip', '-r', '-9', self.compressed_archive_file_path, '.'],
            cwd=self.archive_files_download_dir,
            capture_output=True,
            # stdout=subprocess.DEVNULL
        )
        compressed_size = self.get_size(self.compressed_archive_file_path)
        self.logger.info(
            'Files compressed in %f seconds. Size %f MB. Compression %f',
            time.time()-start_time,
            compressed_size,
            compressed_size/uncompressed_size
        )

    def send_zip_to_archive_compressed_dir(self):
        with open(self.compressed_archive_file_path, 'rb') as f:
            self.logger.info(
                'Uploading compressed archive as %s',
                self.archive_filestore_key
            )
            start_time = time.time()
            self.archive_filestore_dao.post(
                body=f,
                key=self.archive_filestore_key
            )
            self.logger.info('Uploading completed in %f seconds', time.time() - start_time)

    def delete_unzipped_files_from_archive_valid_dir(self):
        self.logger.info('Deleting uncompressed directory %s from archive', self.download_files_key_prefix)
        start_time = time.time()
        number_of_files = self.archive_filestore_dao.delete(
            recursive=True,
            key=self.download_files_key_prefix
        )
        self.logger.info('Deleted %i files in %f seconds', number_of_files, time.time() - start_time)

    def start(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                self.logger.info('Created tmp dir %s', tmpdir)
                start_time = time.time()
                self.create_keys()
                self.create_dirs(tmpdir)
                self.logger.info(
                    'Started archiving directory %s',
                    self.download_files_key_prefix
                )
                self.check_archive_not_exists()
                self.download_files()
                self.zip_files()
                self.send_zip_to_archive_compressed_dir()
                self.delete_unzipped_files_from_archive_valid_dir()
                self.logger.info(
                    'Completed archivation in %f seconds',
                    time.time() - start_time
                )
            except ArchiveExists:
                self.logger.error(
                    'Archive file %s exists. Archivation stopped',
                    self.archive_filestore_key
                )
            except NoFilesToArchive:
                self.logger.warn(
                    'There are no files to archive in %s. Archivation stopped',
                    self.download_files_key_prefix
                )
            except Exception as e:
                self.logger.exception(e)


if __name__ == '__main__':
    ArchiverWorker(
        archive_filestore_dao=filestore.Archive(
            connection_conf=conf.get_s3_env_conf()
        )
    ).start()
