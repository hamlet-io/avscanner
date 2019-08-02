import boto3


class Message:

    def __init__(self, message_res):
        self.id = message_res.message_id
        self.body = message_res.body
        self.receipt_handle = message_res.receipt_handle
        self.attributes = message_res.message_attributes


class Queue:

    def __init__(
        self,
        queue=None,
        connection_conf=None
    ):
        self.sqs = boto3.resource('sqs', **connection_conf)
        self.exceptions = self.sqs.meta.client.exceptions
        self.queue = self.sqs.get_queue_by_name(
            QueueName=queue
        )

    def __to_aws_params(self, **raw_params):
        params = dict()
        for name, value in raw_params.items():
            if value is not None:
                params[name] = value
        return params

    def get(
        self,
        visibility_timeout=None,
        wait_time=None
    ):
        params = self.__to_aws_params(
            VisibilityTimeout=visibility_timeout,
            WaitTimeSeconds=wait_time
        )
        messages = self.queue.receive_messages(
            MaxNumberOfMessages=1,
            **params
        )
        if messages:
            return Message(messages[0])
        return None

    def post(
        self,
        body=None,
        delay=None,
        attributes=None,
        deduplication_id=None,
        group_id=None
    ):
        params = self.__to_aws_params(
            MessageBody=body,
            DelaySeconds=delay,
            MessageAttributes=attributes,
            MessageDeduplicationId=deduplication_id,
            MessageGroupId=group_id
        )
        self.queue.send_message(**params)

    def delete(
        self,
        message=None,
        id=None,
        receipt_handle=None,
    ):
        if message:
            receipt_handle = message.receipt_handle
            id = message.id
        response = self.queue.delete_messages(
            Entries=[
                dict(
                    ReceiptHandle=receipt_handle,
                    Id=id
                )
            ]
        )
        if len(response['Successful']) == 0:
            return False
        return True
