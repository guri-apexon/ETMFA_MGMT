import json
import logging
from kombu import Exchange, Queue, Connection, Queue
from kombu.mixins import ConsumerMixin
from .error_exceptions import ErrorCodes, GenericError
from .service_msg_schema import ErrorMessage


class MessagePublisher:
    def __init__(self, connection_str, exchange_name):
        self.connection_str = connection_str
        self.exchange_name = exchange_name

    def send_str(self, msg_str, queue_name):
        exchange = Exchange(self.exchange_name, type='direct', durable=True)
        queue = Queue(name=queue_name, exchange=exchange,
                      routing_key=queue_name, durable=True)

        with Connection(self.connection_str) as conn:
            with conn.channel() as channel:
                producer = conn.Producer(
                    exchange=exchange, channel=channel, routing_key=queue_name)
                producer.publish(
                    msg_str,
                    declare=[queue],
                    retry=True,
                    retry_policy={
                        'interval_start': 0,  # First retry immediately,
                        # then increase by 20s for every retry.
                        'interval_step': 20,
                        # but don't exceed 300s between retries.
                        'interval_max': 300,
                        'max_retries': 300,  # give up after 300 tries.
                    })

        logging.info("Sent message on queue: {}".format(queue_name))

    def send_dict(self, msg_dict, queue_name):
        try:
            assert queue_name is not None
        except AssertionError as e:
            logging.error('A queue has to be provided!', e)
            raise ValueError('A queue has to be provided')

        jsonstruct = json.dumps(msg_dict)
        self.send_str(jsonstruct, queue_name)


class MessageListenerRunner():
    def __init__(self):
        self.listener = None

    @property
    def is_ready(self):
        return self.listener.is_ready

    def run(self, connection_str, service_name, input_queue_name, output_queue_name, error_queue_name, exchange_name, callback):
        with Connection(connection_str) as conn:
            # consume
            self.listener = MessageListener(conn, connection_str, service_name, input_queue_name, output_queue_name, error_queue_name,
                                            exchange_name, callback)
            self.listener.run()


class MessageListener(ConsumerMixin):
    def __init__(self, connection, connection_str, service_name, input_queue_name, output_queue_name, error_queue_name, exchange_name=None, callback=None):
        self.connection = connection
        self.connection_str = connection_str
        self.exchange_name = exchange_name
        self.execution_context = callback
        self.input_queue_name = input_queue_name
        self.output_queue_name = output_queue_name
        self.error_queue_name = error_queue_name
        self.service_name = service_name
        self.is_ready = False
        self.exchange = Exchange(exchange_name, type='direct', durable=True)

    def get_consumers(self, consumer, channel):
        q = Queue(self.input_queue_name, exchange=self.exchange,
                  routing_key=self.input_queue_name, durable=True)
        return [consumer(queues=[q], callbacks=[self._on_message])]
        
    def on_consume_ready(self, connection, channel, consumers, **kwargs):
        self.is_consumer_ready=True

    def _on_message(self, body, message):
        message_body = None
        queue_name = message.delivery_info['routing_key']
        try:
            message_body = json.loads(body)

        except Exception as ex:
            logging.error("Could not parse message on queue: {}, body: {} {}".format(
                queue_name, body, ex))

        logging.info("Received message on queue: {} and message_body: {}".format(
            queue_name, json.dumps(message_body)[:500]))
        pub = MessagePublisher(self.connection_str, self.exchange_name)
        try:
            if self.execution_context:
                message_body=self.execution_context.on_adapt_msg(message_body)
                message_body = self.execution_context.on_msg(message_body)
            pub.send_dict(message_body, self.output_queue_name)
            logging.info(f"sent message on queue {self.output_queue_name}")
        except Exception as err:
            try:
                if not isinstance(err, GenericError):
                    err = GenericError(ErrorCodes.UNKNOWN_ERROR, str(err))
                err_msg = ErrorMessage(service_name=self.service_name, flow_name=message_body['flow_name'], flow_id=message_body['flow_id'],
                                       error_code=int(err.error_code.value), error_message=err.error_message, error_message_details=err.error_message_details)
                pub.send_str(err_msg.json(), self.error_queue_name)
            except Exception as e:
                logging.error(str(e))
            logging.error(
                f"Fatal message error while processing queue [{queue_name}]:\n Exception message: {str(err)} \n Received message_body: {message_body}")

        finally:
            message.ack()
            if self.execution_context:
                self.execution_context.on_end()
