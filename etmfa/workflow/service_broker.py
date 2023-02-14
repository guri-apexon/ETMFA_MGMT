from abc import ABC, abstractmethod
import ctypes
from .store import WorkFlowStore
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List
import threading
from .messaging import MessageListener, MessagePublisher
from kombu import Connection


class ServiceStatus(Enum):
    STARTING = auto()
    RUNNING = auto()
    STOPPED = auto()
    ERROR = auto()


@dataclass
class ServiceInfo:
    status: ServiceStatus
    info: dict


@dataclass
class RabbitMqInfo:
    exchange_name: str
    message_broker_address: str


@dataclass
class ServiceMessage:
    service_name: str
    service_msg: Dict


@dataclass
class ServicesMesaage:
    msg_list: List[ServiceMessage]


class ServiceBroker(ABC, threading.Thread):
    """
    broker will monitor status of MicroServices 
    broker run in thread calls on_run for inherited class
    """

    def __init__(self):
        self.queues_to_monitor = []
        self.callback = None
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def stop(self):
        thread_id = self.get_id()
        resu = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                          ctypes.py_object(SystemExit))
        if resu > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)

    def add_listener(self, callback):
        self.callback = callback

    def add_queues_to_monitor(self, output_queues):
        """
        from services_info register output queues .As we have completion status on output 
        queues and we listening on them
        start thread only after queues add to monitor
        """
        self.queues_to_monitor = output_queues
        self.start()

    @abstractmethod
    def on_msg(self, queue_name, msg_obj):
        pass

    @abstractmethod
    def send_msg(self, msg_obj, queue_name):
        pass

    @abstractmethod
    def send_msg_list(self, service_msg_map, service_queue_map):
        pass

    @abstractmethod
    def on_run(self):
        pass

    @property
    def is_ready(self):
        pass

    def run(self):
        self.on_run()


class RabbitMqBroker(ServiceBroker):
    def __init__(self, config: RabbitMqInfo, callback=None):
        super().__init__()
        self.callback = callback
        self.config = config
        self.ms_listener = None

    def send_msg(self, msg_obj, queue_name):
        pub = MessagePublisher(
            self.config.message_broker_address, self.config.exchange_name)
        msg_obj_list= msg_obj if isinstance(msg_obj,list) else [msg_obj]
        for msg_obj in msg_obj_list:
            pub.send_msg(msg_obj, queue_name)

    def send_msg_list(self, service_msg_map, service_queue_map):
        pub = MessagePublisher(
            self.config.message_broker_address, self.config.exchange_name)
        pub.multicast_msgs(service_msg_map, service_queue_map)

    def on_msg(self, queue_name, msg_obj):
        self.callback(queue_name, msg_obj)

    @property
    def is_ready(self):
        if not self.ms_listener:
            return False
        return self.ms_listener.is_ready

    def on_run(self):
        with Connection(self.config.message_broker_address) as conn:
            # consume
            self.ms_listener = MessageListener(conn, self.config.message_broker_address,
                                               self.config.exchange_name, self.queues_to_monitor, self.on_msg)
            self.ms_listener.run()
