import common.event
from common import loggers
from common.worker.queue_polling import QueuePollingWorker
from dao.conf import get_s3_env_conf, get_sqs_env_conf
from dao import queue, filestore


logger = loggers.logging.getLogger('VIRUS_SCANNER_WORKER')


class VirusDetected(Exception):
    pass


class VirusScannerWorker(QueuePollingWorker):

    MESSAGE_WAIT_TIME = 10
    MESSAGE_VISIBILITY_TIMEOUT = 10
    SHUTDOWN_CHECK_TIME_INTERVAL = 10
    SHUTDOWN_CHECK_MIN_MESSAGES = 1

    def __init__(
        self,
        virus_scanning_queue_dao=None,
        validation_queue_dao=None,
        quarantine_filestore_dao=None,
        unprocessed_filestore_dao=None
    ):
        super().__init__(
            queue_dao=validation_queue_dao,
            logger=logger
        )
        self.virus_scanning_queue_dao = virus_scanning_queue_dao
        self.validation_queue_dao = validation_queue_dao
        self.quarantine_filestore_dao = quarantine_filestore_dao
        self.unprocessed_filestore_dao = unprocessed_filestore_dao

    def process_message(self, message):
        try:
            event = common.event.loads_s3_object_created_event(message.body)
        except common.event.InvalidEventError as e:
            logger.exception(e)
        self.download_file(event)
        self.scan_file()
        return event is not None

    def scan_file(self):
        pass

    def check_file_size(self, event):
        pass


if __name__ == '__main__':
    s3_connection_data = get_s3_env_conf()
    sqs_connection_data = get_sqs_env_conf()
    VirusScannerWorker(
        virus_scanning_queue_dao=queue.VirusScanning(sqs_connection_data),
        validation_queue_dao=queue.Validation(sqs_connection_data),
        quarantine_filestore_dao=filestore.Quarantine(s3_connection_data),
        unprocessed_filestore_dao=filestore.Unprocessed(s3_connection_data)
    ).start()
