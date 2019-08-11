import os
import subprocess
import common.event
from common import loggers
from common.dao.filestore import FileChangedError
from common.worker.queue_polling import QueuePollingWorker
from dao.conf import (
    get_s3_env_conf,
    get_sqs_env_conf,
    QUARANTINE_BUCKET
)
from dao import queue, filestore


logger = loggers.logging.getLogger('VIRUS_SCANNER_WORKER')


class VirusDetected(Exception):
    pass


class VirusScannerWorker(QueuePollingWorker):

    MESSAGE_WAIT_TIME = 10
    MESSAGE_VISIBILITY_TIMEOUT = 10

    MAX_FILE_SIZE = 1024 * 1024 * int(os.environ['MAX_FILE_SIZE'])  # MB

    FILE_SCAN_DOWNLOAD_PATH = os.environ['DOWNLOAD_PATH_VIRUS_SCAN_FILE']
    VIRUS_SCAN_COMMAND = [
        'clamdscan',
        FILE_SCAN_DOWNLOAD_PATH,
        '--no-summary'
    ]

    def __init__(
        self,
        virus_scanning_queue_dao=None,
        validation_queue_dao=None,
        unprocessed_filestore_dao=None
    ):
        super().__init__(
            queue_dao=virus_scanning_queue_dao,
            logger=logger
        )
        self.virus_scanning_queue_dao = virus_scanning_queue_dao
        self.validation_queue_dao = validation_queue_dao
        self.unprocessed_filestore_dao = unprocessed_filestore_dao

    def process_message(self, message):
        try:
            event = common.event.loads_s3_unprocessed_bucket_object_created_event(message.body)
            self.download_file(event)
            self.scan_file()
            self.forward_to_validator(message)
            self.logger.info(
                'File %s is not a virus, event forwarded to validator',
                event['s3']['object']['key']
            )
            return True
        except VirusDetected:
            self.move_to_qurantine(event)
            return True
        except common.event.InvalidEventError:
            self.logger.error(message.body, exc_info=True)
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

    def scan_file(self):
        self.logger.info('Scanning downloaded file')
        result = subprocess.run(
            self.VIRUS_SCAN_COMMAND,
            capture_output=True,
            encoding='utf8'
        )
        if result.stderr:
            raise Exception(result.stderr)
        if result.returncode == 1:
            raise VirusDetected()
        os.remove(self.FILE_SCAN_DOWNLOAD_PATH)
        self.logger.info('Removed scanned file')

    def download_file(self, event):
        obj = event['s3']['object']
        self.logger.info('Downloading file %s', obj['key'])
        if obj['size'] > self.MAX_FILE_SIZE:
            self.logger.warn('File %s is too large, %i bytes', obj['key'], obj['size'])
            raise VirusDetected()
        self.unprocessed_filestore_dao.download(
            key=obj['key'],
            path=self.FILE_SCAN_DOWNLOAD_PATH,
            etag=obj['eTag']
        )
        self.logger.info('Downloaded file %s', obj['key'])

    def forward_to_validator(self, message):
        self.validation_queue_dao.post(
            body=message.body,
            delay=0
        )

    def move_to_qurantine(self, event):
        obj = event['s3']['object']
        self.unprocessed_filestore_dao.move(
            key=obj['key'],
            etag=obj['eTag'],
            target_key=obj['key'],
            target_bucket=QUARANTINE_BUCKET
        )
        self.logger.warn(
            'Virus detected in %s. Moved to quarantine',
            obj['key']
        )


if __name__ == '__main__':
    s3_connection_data = get_s3_env_conf()
    sqs_connection_data = get_sqs_env_conf()
    VirusScannerWorker(
        virus_scanning_queue_dao=queue.VirusScanning(sqs_connection_data),
        validation_queue_dao=queue.Validation(sqs_connection_data),
        unprocessed_filestore_dao=filestore.Unprocessed(s3_connection_data)
    ).start()
