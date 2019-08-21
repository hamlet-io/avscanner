import json
import dateutil
import posixpath
import common.event
from common.dao.filestore import FileChangedError
from common.worker.queue_polling import QueuePollingWorker
from common import loggers
from dao import (
    queue,
    filestore,
    conf
)


class InvalidFileError(Exception):
    pass


class FileIsNotJSON(InvalidFileError):
    pass


logger = loggers.logging.getLogger('VALIDATOR_WORKER')


class ValidatorWorker(QueuePollingWorker):

    def __init__(
        self,
        validation_queue_dao=None,
        unprocessed_filestore_dao=None
    ):
        super().__init__(
            queue_dao=validation_queue_dao,
            logger=logger
        )
        self.validation_queue_dao = validation_queue_dao
        self.unprocessed_filestore_dao = unprocessed_filestore_dao

    def process_message(self, message):
        try:
            event = common.event.loads_s3_unprocessed_bucket_object_created_event(message.body)
            # download file to verify that it's a valid JSON
            self.download_json_file(event)
            self.logger.info(
                'File %s passed validation',
                event['s3']['object']['key']
            )
            self.move_file_to_valid_dir(event)
            return True
        except common.event.InvalidEventError:
            self.logger.error(message.body, exc_info=True)
            return True
        except FileIsNotJSON:
            self.logger.info(
                'File %s is not JSON',
                event['s3']['object']['key']
            )
            self.move_file_to_invalid_dir(event)
            return True
        except FileChangedError:
            self.logger.warn(
                'File %s changed during processing',
                event['s3']['object']['key']
            )
            return True
        except Exception:
            logger.error('Unexpected error occured', exc_info=True)
            return False

    def download_json_file(self, event):
        obj = event['s3']['object']
        try:
            fileobj = self.unprocessed_filestore_dao.get(
                key=obj['key'],
                etag=obj['eTag']
            )
            if fileobj is None:
                raise FileChangedError()
            return json.loads(fileobj['Body'].read())
        except ValueError as e:
            raise FileIsNotJSON() from e

    def get_archive_key_from_event(self, event, prefix):
        obj = event['s3']['object']
        date = dateutil.parser.parse(event['eventTime']).date()
        private, user, inbox, filename = (part for part in obj['key'].split('/') if part)
        return posixpath.join(prefix, str(date.year), str(date.month), str(date.day), user, filename)

    def move_file_to_archive(self, event, prefix):
        obj = event['s3']['object']
        key = self.get_archive_key_from_event(event, prefix)
        self.unprocessed_filestore_dao.move(
            key=obj['key'],
            etag=obj['eTag'],
            target_key=key,
            target_bucket=conf.ARCHIVE_BUCKET
        )
        self.logger.info('File %s saved into archive as %s', obj['key'], key)

    def move_file_to_valid_dir(self, event):
        self.move_file_to_archive(event, conf.ARCHIVE_BUCKET_VALID_DIR)

    def move_file_to_invalid_dir(self, event):
        self.move_file_to_archive(event, conf.ARCHIVE_BUCKET_INVALID_DIR)


if __name__ == '__main__':
    ValidatorWorker(
        validation_queue_dao=queue.Validation(conf.get_sqs_env_conf()),
        unprocessed_filestore_dao=filestore.Unprocessed(conf.get_s3_env_conf())
    ).start()
