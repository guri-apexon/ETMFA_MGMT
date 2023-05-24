import getpass
import json
import logging as logger
import socket

from kombu import Exchange, Queue
from kombu.mixins import ConsumerMixin
import traceback
from etmfa.consts import Globals

class MessageListener(ConsumerMixin):
    def __init__(self, connection, connection_str, exchange_name=None,queues_to_monitor=None,callback=None):
        self.connection = connection
        self.connection_str = connection_str
        self.exchange_name = exchange_name
        self.queues_to_monitor=queues_to_monitor
        self.callback = callback
        self.logger = logger
        self.is_consumer_ready = True

        if logger is None:
            print("WARNING: No logger used in message listener.")

        self.exchange = Exchange(exchange_name, type='direct', durable=True)

    def get_queues(self):
        return [Queue(q, exchange=self.exchange, routing_key=q, durable=True) for q in self.queues_to_monitor]

    def _create_consumer(self, consumer_cls, queues):
        consumer = consumer_cls(queues=[queues], callbacks=[self._on_message], prefetch_count=5)
        consumer.tag_prefix = f'{socket.gethostname()} - {getpass.getuser()} | Mgmt-{Globals.VERSION} | '

        return consumer

    @property
    def is_ready(self):
        return self.is_consumer_ready

    def get_consumers(self, consumer_cls , channel):
        consumers=[]
        for q in self.get_queues():
            consumers.append(self._create_consumer(consumer_cls, q))
        return consumers

    def on_consume_ready(self, connection, channel, consumers, **kwargs):
        self.is_consumer_ready=True
        
    def _on_message(self, body, message):
        message_body = None
        queue_name = message.delivery_info['routing_key']
        try:
            message_body = json.loads(body)

        except Exception as ex:
            self.logger.error("Could not parse message on queue: {}, body: {} {}".format(queue_name, body, ex))

        self.logger.debug("Received message on queue: {} and message_body: {}".format(queue_name, json.dumps(message_body)[:500]))

        try:
            if self.is_ready:
                self.callback(queue_name,message_body)

        except Exception as ex:
            traceback.print_exc()
            self.logger.error(f"Fatal message error while processing queue [{queue_name}]:\n Exception message: {str(ex)} \n Received message_body: {message_body}")
        finally:
            message.ack()


