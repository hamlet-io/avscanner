import os
import datetime
import pytz
import common.event
from dao import (
    queue,
    filestore,
    conf
)
from common.loggers import logging


default_logger = logging.getLogger('UNPROCESSED_FILES_AUDITOR')


class FileMovedError(Exception):
    pass


class UnprocessedFilesAuditorWorker:

    TIMEZONE = pytz.timezone(os.environ['ARCHIVE_TIMEZONE'])
    RESEND_INTERVAL = int(os.environ['AUDIT_EVENT_RESEND_INTERVAL'])

    def __init__(
        self,
        virus_scanning_queue_dao=None,
        unprocessed_filestore_dao=None,
        logger=None
    ):
        self.logger = logger if logger else default_logger
        self.virus_scanning_queue_dao = virus_scanning_queue_dao
        self.unprocessed_filestore_dao = unprocessed_filestore_dao

    def get_utc_now(self):  # pragma: no cover
        return datetime.datetime.utcnow()

    def load_file(self, key):
        file = self.unprocessed_filestore_dao.get(key)
        if file is None:
            raise FileMovedError()
        return file

    def try_to_resend_file_put_event(self, key, now):
        self.logger.info('Checking file %s', key)
        file = None
        submission_time = None
        try:
            try:
                # using filename to get time when it was submitted
                user, submission_time, upload_hash = common.event.parse_unprocessed_file_key(key)
                submission_time = submission_time.astimezone(self.TIMEZONE)
            except common.event.InvalidKeyFormat:
                # handling invalid key scenario, highly improbable, but may happen
                self.logger.error('Invalid key format: %s. Loading file to check last mod time', key)
                file = self.load_file(key)
                submission_time = file['LastModified'].astimezone(self.TIMEZONE)

            self.logger.info('File submission time:%s', submission_time.isoformat())
            if now - submission_time < datetime.timedelta(seconds=self.RESEND_INTERVAL):
                self.logger.info('Event resend is not needed')
                return
            # saving time if file loaded in invalid key scenario
            if not file:
                file = self.load_file(key)
            # creating mininal required fields in event
            event = common.event.create_minimal_valid_file_put_event(
                key=key,
                etag=file['ETag'],
                size=file['ContentLength'],
                bucket=self.unprocessed_filestore_dao.bucket.name,
                event_time=submission_time
            )
            self.logger.info('Resending put event')
            # pushing event to virus scanner queue
            self.virus_scanning_queue_dao.post(
                event,
                delay=0
            )
        except FileMovedError:
            self.logger.info('File %s is no longer accessible. Skip.', key)

    def start(self):
        # There aren't a lot of exceptions which it can handle
        # and everything should end up in sentry logs anyway.
        # Therefore there is no custom logging here except invalid key scenario & file moved error
        now = self.get_utc_now().astimezone(self.TIMEZONE)
        self.logger.info('Starting. NOW: %s', now.isoformat())
        for key in self.unprocessed_filestore_dao.list():
            self.try_to_resend_file_put_event(key, now)


if __name__ == '__main__':
    UnprocessedFilesAuditorWorker(
        virus_scanning_queue_dao=queue.VirusScanning(conf.get_sqs_env_conf()),
        unprocessed_filestore_dao=filestore.Unprocessed(conf.get_s3_env_conf())
    )
