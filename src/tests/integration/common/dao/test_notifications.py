from processor.common.dao.notifications import Notifications
from tests.integration.conftest import (
    VIRUS_NOTIFICATION_TOPIC,
    SNS_CONNECTION_DATA,
)


def test():
    notifications = Notifications(
        topic=VIRUS_NOTIFICATION_TOPIC,
        connection_conf=SNS_CONNECTION_DATA
    )
    # test json message
    notifications.post({'Message': 'Hello world!'})
    # # test non json message
    notifications.post('Hello world!')
