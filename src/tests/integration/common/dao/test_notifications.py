import pytest
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
    notifications.post({
        'default': 'Default hello world!',
        'Message': 'Hello world!'
    })
    # json without default field must throw exception
    with pytest.raises(ValueError):
        notifications.post({
            'Message': 'JSON without default!'
        })
    # test non json message
    notifications.post('Hello world!')
