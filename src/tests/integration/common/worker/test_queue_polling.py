import os
import datetime
from unittest import mock
from processor.dao import queue, conf
from processor.common.worker.queue_polling import QueuePollingWorker


def test(clear_queues):
    clear_queues()

    def successful_processing(message):
        return True

    def failed_processing(message):
        return False

    queue_dao = queue.VirusScanning(conf.get_sqs_env_conf())

    worker = QueuePollingWorker(queue_dao=queue_dao)
    worker.MESSAGE_VISIBILITY_TIMEOUT = 0
    worker.MESSAGE_WAIT_TIME = 0

    assert iter(worker) is worker
    assert not next(worker)

    queue_dao.post(body='Hello', delay=0)

    worker.process_message = failed_processing
    assert next(worker)
    assert queue_dao.get(wait_time=0, visibility_timeout=0)

    worker.process_message = successful_processing
    assert next(worker)
    assert not queue_dao.get(wait_time=0, visibility_timeout=0)

    # test startup time logging
    class Worker(QueuePollingWorker):
        def __next__(self):
            raise StopIteration()

    worker = Worker()
    worker.start()
    with mock.patch.dict(os.environ):
        try:
            del os.environ['START_TIMESTAMP']
        except KeyError:
            pass
        worker.start()
    with mock.patch.dict(os.environ, {'START_TIMESTAMP': str(int(datetime.datetime.now().timestamp()))}):
        worker.start()
    with mock.patch.dict(os.environ, {'START_TIMESTAMP': 'BAD TIME'}):
        worker.start()
