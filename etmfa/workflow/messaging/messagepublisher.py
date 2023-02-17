import json
import logging
from kombu import Connection, Exchange, Queue
from etmfa.consts import Consts as consts

logger = logging.getLogger(consts.LOGGING_NAME)


class MessagePublisher:
    def __init__(self, connection_str, exchange_name):
        self.connection_str = connection_str
        self.exchange_name = exchange_name
        self.initial_msg = True

    def _purge_on_start(self, channel, queue_name):
        """
        purge queue messages on start
        """
        if self.initial_msg:
            try:
                channel.queue_purge(queue_name)
            except Exception as e:
                pass
            self.initial_msg = False

    def _publish_msg(self, conn, exchange, channel, queue_name, msg_dict):
        msg_str = json.dumps(msg_dict)
        logger.debug(f'message sent on {queue_name} is {msg_str}')
        queue = Queue(name=queue_name, exchange=exchange,
                      routing_key=queue_name, durable=True)
        producer = conn.Producer(
            exchange=exchange, channel=channel, routing_key=queue_name)
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

    def multicast_msgs(self, msg_obj_map, queues_map):
        """
        msg_obj can be of list type as well,mulitple messages for same queue
        """
        exchange = Exchange(self.exchange_name, type='direct', durable=True)
        with Connection(self.connection_str) as conn:
            with conn.channel() as channel:
                for service_name, queue_name in queues_map.items():
                    msg_obj = msg_obj_map.get(service_name,None)
                    if not msg_obj:
                        continue
                    msg_obj_list= msg_obj if isinstance(msg_obj,list) else [msg_obj]
                    for msg_obj in msg_obj_list:
                        self._publish_msg(conn, exchange, channel,
                                        queue_name, msg_obj)

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


    def send_msg(self, msg_dict, queue_name):
        try:
            assert queue_name is not None
        except AssertionError as e:
            # logger.error('A queue has to be provided!', e)
            raise ValueError('A queue has to be provided')

        jsonstruct = json.dumps(msg_dict)
        self.send_str(jsonstruct, queue_name)
