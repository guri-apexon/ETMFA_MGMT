import getpass
import json
import logging
import socket

from kombu import Exchange, Queue
from kombu.mixins import ConsumerMixin

from etmfa.consts import Consts as consts
from etmfa.consts import Globals
from etmfa.messaging.messagepublisher import MessagePublisher
from etmfa.messaging.models import queue_names

logger = logging.getLogger(consts.LOGGING_NAME)


class MessageListener(ConsumerMixin):
    def __init__(self, connection, connection_str, exchange_name=None, queue_callback_dict={}, logger=None):
        self.connection = connection
        self.connection_str = connection_str
        self.exchange_name = exchange_name
        self.queue_callback_dict = queue_callback_dict
        self.logger = logger

        if logger is None:
            print("WARNING: No logger used in message listener.")

        self.exchange = Exchange(exchange_name, type='direct', durable=True)

    def get_queues(self):
        return [Queue(q, exchange=self.exchange, routing_key=q, durable=True) for q in self.queue_callback_dict.keys()]

    def _create_consumer(self, Consumer, queues):
        consumer = Consumer(queues=[queues], callbacks=[self._on_message], prefetch_count=5)
        consumer.tag_prefix = f'{socket.gethostname()} - {getpass.getuser()} | Mgmt-{Globals.VERSION} | '

        return consumer

    def get_consumers(self, Consumer, channel):
        return [self._create_consumer(Consumer, q) for q in self.get_queues()]


    # def build_queue_callback(queue_names):
    #     queue_names.add_listener(COMPARE.queues)

    def add_listener(self, queue_name, callback):
        """
        Add a queue listener with the mapped callback to be invoked whenever a message is received. Listeners cannot
        be added after calling 'run()'

        queue_name: string callback: Function with the signature (dictionary_object, message publisher), where the
        dictionary_object corresponds to the received message.

        Note: Only one top-level callback can be registered per queue.
        """
        if not queue_name:
            raise ValueError("Queue name parameter must be non-empty or whitespace: {}".format(queue_name))

        if queue_name in self.queue_callback_dict:
            raise ValueError(
                "Only one callback can be registered for a single queue. If multiple callbacks are required, "
                "compose functions.")

        self.queue_callback_dict[queue_name] = callback

    def _on_message(self, body, message):
        queue_name = message.delivery_info['routing_key']
        try:

            message_body = json.loads(body)

            Globals.THREAD_LOCAL.aidocid = message_body.get('id')
        except Exception as ex:
            logger.error("Could not parse message on queue: {}, body: {} {}".format(queue_name, body, ex))

        logger.info("Received message on queue: {}".format(queue_name))

        try:
            self.queue_callback_dict[queue_name](
                json.loads(body),
                #json.loads(json.dumps(body)),
                MessagePublisher(self.connection_str, self.exchange_name)
            )
            message.ack()
        except Exception as ex:
            logger.error("Fatal message error while processing queue: {}, {}".format(queue_name, ex))


