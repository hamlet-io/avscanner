from .conf import VIRUS_NOTIFICATION_TOPIC
from common.dao.notifications import Notifications


class Virus(Notifications):

    def __init__(self, connection_conf=None):
        super().__init__(
            topic=VIRUS_NOTIFICATION_TOPIC,
            connection_conf=connection_conf
        )
