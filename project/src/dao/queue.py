from common.dao.queue import Queue
from .conf import (
    VALIDATION_QUEUE,
    VIRUS_SCANNING_QUEUE
)


class VirusScanning(Queue):
    def __init__(self, connection_conf=None):
        super().__init__(
            queue=VIRUS_SCANNING_QUEUE,
            connection_conf=connection_conf
        )


class Validation(Queue):
    def __init__(self, connection_conf=None):
        super().__init__(
            queue=VALIDATION_QUEUE,
            connection_conf=connection_conf
        )
