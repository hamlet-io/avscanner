import time
import pytest
from common.dao.queue import Queue
from tests.integration.conftest import (
    SQS_CONNECTION_DATA,
    VALIDATION_QUEUE
)


@pytest.mark.usefixtures(
    'clear_queues'
)
def test():
    queue = Queue(
        queue=VALIDATION_QUEUE,
        connection_conf=SQS_CONNECTION_DATA
    )
    # test queue is empty
    assert queue.get(wait_time=1) is None
    # testing post -> get -> delete without delays
    body = 'Message'
    queue.post(body, delay=0)
    message = queue.get()
    assert message.body == body
    assert queue.delete(message=message)
    assert queue.get() is None

    # testing delayed post
    body = 'Hello'
    queue.post(body, delay=1)
    assert not queue.get()
    message = queue.get(wait_time=1)
    assert message
    assert message.body == body
    assert queue.delete(message=message)

    # testing visibility_timeout
    body = 'Visibility'
    queue.post(body, delay=0)
    message = queue.get(visibility_timeout=1)
    assert message
    assert message.body == body
    assert not queue.get()
    message = queue.get(wait_time=1)
    assert message
    assert message.body == body
    assert queue.delete(message=message)

    messages = [
        'one',
        'two',
        'three',
        'four'
    ]

    for body in messages:
        queue.post(body=body, delay=0)
    for body in messages:
        message = queue.get(visibility_timeout=1, wait_time=0)
        assert message
        assert message.body == body
    assert not queue.get()
    time.sleep(1.5)
    for body in messages:
        message = queue.get(wait_time=0)
        assert message
        assert message.body == body
        assert queue.delete(message=message)
    assert not queue.get(wait_time=1)

    # assert not queue.delete(id='Invalid', receipt_handle='Invalid')
