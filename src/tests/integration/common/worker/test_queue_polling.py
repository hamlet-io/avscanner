import pytest
from processor.dao import queue, conf
from processor.common.worker.queue_polling import QueuePollingWorker


@pytest.mark.usefixtures(
    'clear_queues'
)
def test():

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


@pytest.mark.usefixtures(
    'clear_queues'
)
def test_shutdown():
    queue_dao = queue.VirusScanning(conf.get_sqs_env_conf())
    worker = QueuePollingWorker(queue_dao=queue_dao)

    worker.SHUTDOWN_CHECK_MIN_MESSAGES = 3
    worker.SHUTDOWN_CHECK_TIME_INTERVAL = 4
    worker.MESSAGE_WAIT_TIME = 1
    worker.MESSAGE_VISIBILITY_TIMEOUT = 60
    worker.process_message = lambda m: True

    counter = 0
    messages = 5
    for i in range(messages):
        queue_dao.post(body=str(i), delay=i+1)
    for result in worker:
        counter += 1 if result else 0
    assert counter == messages
