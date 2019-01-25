import json

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

from .messagepublisher import MessagePublisher


class MessageListener(ConsumerMixin):
    def __init__(self, connection, connection_str, exchange_name=None, queue_callback_dict={}, logger=None):
        self.connection = connection
        self.connection_str = connection_str
        self.exchange_name = exchange_name
        self.queue_callback_dict = queue_callback_dict
        self.logger = logger

        if logger == None:
            print("WARNING: No logger used in message listener.")

        self.exchange = Exchange(exchange_name, type='direct', durable=True)


    def get_queues(self):
        return [Queue(q, exchange=self.exchange, routing_key=q, durable=False) for q in self.queue_callback_dict.keys()]

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[q], callbacks=[self._on_message]) for q in self.get_queues()]

    def add_listener(self, queue_name, callback):
        """
        Add a queue listener with the mapped callback to be invoked whenever a message is received. Listeners cannot be added after calling 'run()'

        queue_name: string
        callback: Function with the signature (dictionary_object, message publisher), where the dictionary_object corresponds to the received message.

        Note: Only one top-level callback can be registered per queue.
        """
        if not queue_name:
            raise ValueError("Queue name parameter must be non-empty or whitespace: {}".format(queue_name))

        if queue_name in self.queue_callback_dict:
            raise ValueError("Only one callback can be registered for a single queue. If multiple callbacks are required, compose functions.")

        self.queue_callback_dict[queue_name] = callback
    
    def _on_message(self, body, message):
        queue_name = message.delivery_info['routing_key']

        self.logger.info("Received message on queue: {}".format(queue_name))

        try:
            callback = self.queue_callback_dict[queue_name](
                    json.loads(body),
                    MessagePublisher(self.connection_str, self.exchange_name, self.logger)
                )
            message.ack()
        except Exception as ex:
            self.logger.error("Fatal message error while processing queue: {}".format(queue_name), ex)