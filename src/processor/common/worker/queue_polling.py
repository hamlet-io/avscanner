import time
from common import loggers


queue_polling_worker_logger = loggers.logging.getLogger('QUEUE_POLLING_WORKER')


class QueuePollingWorker:

    MESSAGE_WAIT_TIME = 0
    MESSAGE_VISIBILITY_TIMEOUT = 0
    SHUTDOWN_CHECK_TIME_INTERVAL = 60
    SHUTDOWN_CHECK_MIN_MESSAGES = 1

    def __init__(self, queue_dao=None, logger=None):
        self.__queue = queue_dao
        self.logger = logger if logger else queue_polling_worker_logger
        self.__shutdown_check_time = 0
        self.__shutdown_check_messages_received = 0
        self.__stop = False

    def __iter__(self):
        return self

    def __next__(self):
        if self.__stop:
            self.logger.info(
                'Shutdown. Messages %i/%i in %i seconds.',
                self.__shutdown_check_messages_received,
                self.SHUTDOWN_CHECK_MIN_MESSAGES,
                self.SHUTDOWN_CHECK_TIME_INTERVAL
            )
            raise StopIteration()

        started_time = time.time()

        message = self.__queue.get(
            wait_time=self.MESSAGE_WAIT_TIME,
            visibility_timeout=self.MESSAGE_VISIBILITY_TIMEOUT
        )

        if message is not None:
            self.logger.info('Message received.')
            self.__shutdown_check_messages_received += 1
            if self.process_message(message):
                self.logger.info('Message processed succesfully, deleting message.')
                self.__queue.delete(message=message)
            else:
                self.logger.info('Message processing failed.')

        self.__shutdown_check_time += time.time() - started_time
        if self.__shutdown_check_time >= self.SHUTDOWN_CHECK_TIME_INTERVAL:
            if self.__shutdown_check_messages_received < self.SHUTDOWN_CHECK_MIN_MESSAGES:
                self.__stop = True
            else:
                self.__shutdown_check_messages_received = 0

        return message is not None

    def process_message(self, message):  # pragma: no cover
        return True

    def start(self):  # pragma: no cover
        self.logger.info('Started.')
        try:
            for result in self:
                pass
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.logger.exception(e)
