from common.dao.filestore import FileStore
from .conf import (
    QUARANTINE_BUCKET,
    UNPROCESSED_BUCKET,
    ARCHIVE_BUCKET
)


class Quarantine(FileStore):
    def __init__(self, connection_conf=None):
        super().__init__(
            bucket=QUARANTINE_BUCKET,
            connection_conf=connection_conf
        )


class Archive(FileStore):
    def __init__(self, connection_conf=None):
        super().__init__(
            bucket=ARCHIVE_BUCKET,
            connection_conf=connection_conf
        )


class Unprocessed(FileStore):
    def __init__(self, connection_conf=None):
        super().__init__(
            bucket=UNPROCESSED_BUCKET,
            connection_conf=connection_conf
        )
