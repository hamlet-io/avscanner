from src.dao import queue
from src.dao import conf


def test():
    queue.Validation(conf.get_sqs_env_conf())
    queue.VirusScanning(conf.get_sqs_env_conf())
