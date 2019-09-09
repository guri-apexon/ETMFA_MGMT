import os, logging, json

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

class MessagePublisher:
        def __init__(self, connection_str, exchange_name, logger):
            self.connection_str = connection_str
            self.exchange_name = exchange_name
            self.logger = logger

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
                            'interval_start': 0, # First retry immediately,
                            'interval_step': 20,  # then increase by 20s for every retry.
                            'interval_max': 300,  # but don't exceed 300s between retries.
                            'max_retries': 300,   # give up after 300 tries.
                        })

            self.logger.info("Sent message on queue: {}".format(queue_name))

        def send_obj(self, msg_obj):
            try:
                assert msg_obj.QUEUE_NAME != None and msg_obj.QUEUE_NAME != ''
            except AssertionError as e:
                self.logger.error('Object must be serializable and contain a queue name definition!', e)
                raise ValueError('Object must be serializable and contain a queue name definition!')
            jsonstruct = json.dumps(msg_obj.__dict__)
            self.send_str(jsonstruct, msg_obj.QUEUE_NAME)
