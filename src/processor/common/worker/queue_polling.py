from common import loggers


queue_polling_worker_logger = loggers.logging.getLogger('QUEUE_POLLING_WORKER')


class QueuePollingWorker:

    MESSAGE_WAIT_TIME = 0
    MESSAGE_VISIBILITY_TIMEOUT = 0

    def __init__(self, queue_dao=None, logger=None):
        self.__queue = queue_dao
        self.logger = logger if logger else queue_polling_worker_logger

    def __iter__(self):
        return self

    def __next__(self):
        self.logger.info(
            'Getting message. Wait time: %s seconds. Visibility Timeout: %s seconds',
            self.MESSAGE_WAIT_TIME,
            self.MESSAGE_VISIBILITY_TIMEOUT
        )
        message = self.__queue.get(
            wait_time=self.MESSAGE_WAIT_TIME,
            visibility_timeout=self.MESSAGE_VISIBILITY_TIMEOUT
        )

        if message is not None:
            self.logger.info('Message received:%s', message.id)
            # self.logger.info(message.body)
            if self.process_message(message):
                self.logger.info('Message processed succesfully, deleting message.')
                self.__queue.delete(message=message)
            else:
                self.logger.info('Message processing failed.')

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
