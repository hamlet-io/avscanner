import json
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


class InvalidJSONFileSchema(InvalidFileError):
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
            data = self.download_json_file(event)
            self.validate_json_file_schema(data)
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
        except InvalidJSONFileSchema:
            self.logger.info(
                'File %s has invalid schema',
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
        except Exception as e:
            logger.error('Unexpected error occured', e)
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

    def validate_json_file_schema(self, data):
        # TODO: create proper schema validation.
        # Maybe we should use marshmallow for verbose
        # schema validation
        try:
            data['name']['first']
            data['name']['last']
        except KeyError as e:
            raise InvalidJSONFileSchema() from e

    def move_file_to_archive(self, event, prefix):
        obj = event['s3']['object']
        self.unprocessed_filestore_dao.move(
            key=obj['key'],
            etag=obj['eTag'],
            target_key=posixpath.join(
                prefix,
                obj['key']
            ),
            target_bucket=conf.ARCHIVE_BUCKET
        )

    def move_file_to_valid_dir(self, event):
        self.logger.info(
            'File %s moved to archive valid dir',
            event['s3']['object']['key']
        )
        self.move_file_to_archive(event, conf.ARCHIVE_BUCKET_VALID_DIR)

    def move_file_to_invalid_dir(self, event):
        self.logger.info(
            'File %s moved to archive invalid dir',
            event['s3']['object']['key']
        )
        self.move_file_to_archive(event, conf.ARCHIVE_BUCKET_INVALID_DIR)


if __name__ == '__main__':
    ValidatorWorker(
        validation_queue_dao=queue.Validation(conf.get_sqs_env_conf()),
        unprocessed_filestore_dao=filestore.Unprocessed(conf.get_s3_env_conf())
    ).start()
