import json
import logging

from kombu import Connection, Exchange, Queue

from etmfa.consts import Consts as consts

logger = logging.getLogger(consts.LOGGING_NAME)


class MessagePublisher:
    def __init__(self, connection_str, exchange_name):
        self.connection_str = connection_str
        self.exchange_name = exchange_name

    def send_str(self, msg_str, queue_name):
        exchange = Exchange(self.exchange_name, type='direct', durable=True)
        queue = Queue(name=queue_name, exchange=exchange, routing_key=queue_name, durable=True)

        with Connection(self.connection_str) as conn:
            with conn.channel() as channel:
                producer = conn.Producer(exchange=exchange, channel=channel, routing_key=queue_name)
                producer.publish(
                    msg_str,
                    declare=[queue],
                    retry=True,
                    retry_policy={
                        'interval_start': 0,  # First retry immediately,
                        'interval_step': 20,  # then increase by 20s for every retry.
                        'interval_max': 300,  # but don't exceed 300s between retries.
                        'max_retries': 300,  # give up after 300 tries.
                    })

        logger.info("Sent message on queue: {}".format(queue_name))

    def send_obj(self, msg_obj):
        self.send_dict(msg_obj.__dict__, msg_obj.QUEUE_NAME)

    def send_dict(self, msg_dict, queue_name):
        try:
            assert queue_name is not None
        except AssertionError as e:
            logger.error('A queue has to be provided!', e)
            raise ValueError('A queue has to be provided')

        jsonstruct = json.dumps(msg_dict)
        self.send_str(jsonstruct, queue_name)
