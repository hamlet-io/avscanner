import time


class QueuePollingWorker:

    MESSAGE_WAIT_TIME = 0
    MESSAGE_VISIBILITY_TIMEOUT = 0
    SHUTDOWN_CHECK_TIME_INTERVAL = 60
    SHUTDOWN_CHECK_MIN_MESSAGES = 1

    def __init__(self, queue_dao):
        self.__queue = queue_dao
        self.__shutdown_check_time = 0
        self.__shutdown_check_messages_received = 0

    def __iter__(self):
        return self

    def __next__(self):
        started_time = time.time()

        message = self.__queue.get(
            wait_time=self.MESSAGE_WAIT_TIME,
            visibility_timeout=self.MESSAGE_VISIBILITY_TIMEOUT
        )

        if message is not None:
            self.__shutdown_check_messages_received += 1

        if self.process_message(message):
            self.__queue.delete(message=message)

        self.__shutdown_check_time += time.time() - started_time
        if self.__shutdown_check_time >= self.SHUTDOWN_CHECK_TIME_INTERVAL:
            if self.__shutdown_check_messages_received < self.SHUTDOWN_CHECK_MIN_MESSAGES:
                raise StopIteration()
            else:
                self.__shutdown_check_messages_received = 0
        return True

    def process_message(self, message):
        return True

    def start(self):
        try:
            for result in self:
                pass
        except KeyboardInterrupt:
            pass
