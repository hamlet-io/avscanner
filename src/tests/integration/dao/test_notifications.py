from unittest import mock
from processor.dao import notifications
from processor.dao import conf


def test():
    notifications.Virus(conf.get_sns_env_conf())


@mock.patch('processor.dao.notifications.VIRUS_NOTIFICATION_TOPIC', None)
def test_no_name_initialization():
    assert notifications.VIRUS_NOTIFICATION_TOPIC is None
    notifications.Virus(conf.get_sns_env_conf())
