import os
import time
import posixpath
import subprocess
import shutil
import datetime
from common import loggers
from dao import (
    conf,
    filestore
)

default_logger = loggers.logging.getLogger('ARCHIVER_WORKER')

ARCHIVE_DOWNLOAD_DIR = os.environ['DOWNLOAD_PATH_ARCHIVED_FILES']
COMPRESSED_ARCHIVE_FILE_PATH = os.environ['COMPRESSED_ARCHIVE_FILE_PATH']
ARCHIVE_FILENAME = 'archive.zip'


class NoFilesToArchive(Exception):
    pass


class ArchiveExists(Exception):
    pass


class ArchiverWorker:

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

    def remove(self, target):
        shutil.rmtree(target, ignore_errors=True)

    # for easy mocking
    def get_current_date(self):
        return datetime.datetime.utcnow().date()

    # this will return last day of previous month
    # meaning that created archive will contain files uploaded last month
    def get_archive_date(self):
        date = self.get_current_date()
        date.replace(day=1)
        date -= datetime.timedelta(days=1)
        return date

    def get_download_files_prefix(self):
        return self.get_archive_date().strftime('%Y/%-m/')

    def clear_download_dir(self):
        self.remove(ARCHIVE_DOWNLOAD_DIR)
        self.logger.info('Deleted %s directory and content', ARCHIVE_DOWNLOAD_DIR)
        os.makedirs(ARCHIVE_DOWNLOAD_DIR, exist_ok=True)
        self.logger.info('Created empty %s directory', ARCHIVE_DOWNLOAD_DIR)

    def cleanup(self):
        self.logger.info('Cleaning up...')
        self.remove(ARCHIVE_DOWNLOAD_DIR)
        self.remove(COMPRESSED_ARCHIVE_FILE_PATH)
        self.logger.info('Cleanup completed')

    def get_archive_filestore_key(self, prefix):
            return posixpath.join(
                conf.ARCHIVE_BUCKET_COMPRESSED_DIR,
                prefix,
                ARCHIVE_FILENAME
            )

    def check_archive_not_exists(self, prefix):
        key = self.get_archive_filestore_key(prefix)
        self.logger.info('Checking that archive file %s does not exist...', key)
        if self.archive_filestore_dao.get(key=key) is not None:
            raise ArchiveExists()
        self.logger.info('Archive file %s not found. Continuing...')

    def download_files(self, prefix):
        self.logger.info('Downloading valid files from %s to %s', prefix, ARCHIVE_DOWNLOAD_DIR)
        number_of_files = self.archive_filestore_dao.download(
            recursive=True,
            key=prefix,
            path=ARCHIVE_DOWNLOAD_DIR
        )
        if number_of_files == 0:
            raise NoFilesToArchive()
        size = self.get_size(ARCHIVE_DOWNLOAD_DIR)
        self.logger.info('Downloaded %i files from %s. Size %f MB', number_of_files, prefix, size)

    def zip_files(self, prefix):
        self.logger.info('Starting compression...')
        uncompressed_size = self.get_size(ARCHIVE_DOWNLOAD_DIR)
        start_time = time.time()
        subprocess.run(
            ['zip', '-r', '-9', COMPRESSED_ARCHIVE_FILE_PATH, '.'],
            cwd=ARCHIVE_DOWNLOAD_DIR,
            stdout=subprocess.DEVNULL
        )
        compressed_size = self.get_size(COMPRESSED_ARCHIVE_FILE_PATH)
        self.logger.info(
            'Files compressed in %f seconds. Size %f MB. Compression %f',
            time.time()-start_time,
            compressed_size,
            compressed_size/uncompressed_size
        )
        self.remove(ARCHIVE_DOWNLOAD_DIR)
        self.logger.info('Local uncompressed archive copy deleted')

    def send_zip_to_archive_compressed_dir(self, prefix):
        with open(COMPRESSED_ARCHIVE_FILE_PATH, 'rb') as f:
            key = self.get_archive_filestore_key(prefix)
            self.logger.info('Uploading compressed archive as %s', key)
            start_time = time.time()
            self.archive_filestore_dao.post(
                body=f,
                key=key
            )
            self.logger.info('Uploading completed in %f seconds', time.time() - start_time)
        os.remove(COMPRESSED_ARCHIVE_FILE_PATH)
        self.logger.info('Local compressed archive copy deleted')

    def delete_unzipped_files_from_archive_valid_dir(self, prefix):
        self.logger.info('Deleting uncompressed directory %s from archive', prefix)
        start_time = time.time()
        number_of_files = self.archive_filestore_dao.delete(
            recursive=True,
            key=prefix
        )
        self.logger.info('Deleted %i files in %f seconds', number_of_files, time.time() - start_time)

    def start(self):
        try:
            start_time = time.time()
            prefix = self.get_download_files_prefix()
            self.logger.info('Started archiving directory %s', prefix)
            self.check_archive_not_exists(prefix)
            self.clear_download_dir()
            self.download_files(prefix)
            self.zip_files(prefix)
            self.send_zip_to_archive_compressed_dir(prefix)
            self.delete_unzipped_files_from_archive_valid_dir(prefix)
            self.logger.info('Completed archivation in %f seconds', time.time() - start_time)
        except ArchiveExists:
            self.logger.error('Archive file %s exists. Archivation stopped', self.get_archive_filestore_key(prefix))
        except NoFilesToArchive:
            self.logger.warn('There are no files to archive in %s. Archivation stopped', prefix)
        except Exception as e:
            self.logger.exception(e)
        finally:
            self.cleanup()


if __name__ == '__main__':
    ArchiverWorker(
        archive_filestore_dao=filestore.Archive(
            connection_conf=conf.get_s3_env_conf()
        )
    ).start()
