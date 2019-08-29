import json
import boto3


class Notifications:

    def __init__(
        self,
        topic=None,
        connection_conf=None
    ):
        self.sns = boto3.resource('sns', **connection_conf)
        self.__topic_name = topic

    @property
    def topic(self):
        try:
            return self.__topic
        except AttributeError:
            self.__topic = self.sns.Topic(self.__topic_name)
            return self.__topic

    def post(
        self,
        body=None
    ):
        if isinstance(body, dict):
            params = dict(
                Message=json.dumps(body),
                MessageStructure='json'
            )
        else:
            params = dict(
                Message=body,
                MessageStructure='string'
            )
        self.topic.publish(**params)
        return True
