from unittest import mock
from processor.dao import queue
from processor.dao import conf


def test():
    queue.Validation(conf.get_sqs_env_conf())
    queue.VirusScanning(conf.get_sqs_env_conf())


@mock.patch('processor.dao.queue.VALIDATION_QUEUE', None)
@mock.patch('processor.dao.queue.VIRUS_SCANNING_QUEUE', None)
def test_no_name_initialization():
    assert queue.VALIDATION_QUEUE is None
    assert queue.VIRUS_SCANNING_QUEUE is None
    queue.Validation(conf.get_sqs_env_conf())
    queue.VirusScanning(conf.get_sqs_env_conf())
