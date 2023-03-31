
import time
from abc import abstractmethod, ABC
import threading
from pydantic import BaseModel
from .db.schemas import  MsRegistry
from .db.db_utils import Store
from .service_msg_schema import CompositeServiceMessage, ServiceMessage
from .message_broker import initialize_msg_listeners


class ContextData(BaseModel):
    command: str
    data: dict = {}


class ExecutionContext(threading.Thread):
    """
    on_msg:message callback 
    """

    def __init__(self, context_max_active_time):
        self.last_active = time.time()
        self._context_max_active_time = context_max_active_time
        self.thread_wait_time = int(
            self._context_max_active_time/2)  # keep minute atleast
        self.context_alive = False
        self.keep_running = True
        self.num_executions = 0
        self.th_lock = threading.Lock()
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.start()

    @abstractmethod
    def on_init(self):
        pass

    @abstractmethod
    def on_callback(self, data):
        pass

    @abstractmethod
    def on_release(self):
        pass

    @property
    def context_max_active_time(self):
        return self._context_max_active_time

    @context_max_active_time.setter
    def context_max_active_time(self, val):
        self._context_max_active_time = val

    def destroy_context(self):
        """
        while message is processing context should be destroyed
        """
        with self.th_lock:
            self.on_release()

    def on_msg(self, msg):
        """
        application is blocked untill message is processed ,because of lock
        this is the behaviour we need .
        """
        with self.th_lock:
            self.last_active = time.time()
            if not self.context_alive:
                self.on_init()
        recv_msg = CompositeServiceMessage(**msg)
        flow_id = recv_msg.flow_id
        flow_name = recv_msg.flow_name
        service_params = {}
        for sr_info in recv_msg.services_param:
            service_params[sr_info.service_name] = sr_info.params
        out_param = self.on_callback(service_params)
        if not isinstance(out_param, dict):
            out_param = {}
        service_msg = ServiceMessage(
            flow_name=flow_name, flow_id=flow_id, params=out_param).dict()
        return service_msg

    def on_end(self):
        self.num_executions += 1

    def stop(self):
        with self.th_lock:
            self.keep_running = False

    def is_running(self):
        with self.th_lock:
            return self.keep_running

    def run(self):
        while (self.is_running()):
            curr_time = time.time()
            diff = self.last_active-curr_time
            if diff >= self._context_max_active_time:
                self.destroy_context()
                self.context_alive = False
            time.sleep(self.thread_wait_time)


class MicroServiceWrapper(ABC):

    def __init__(self, config):
        # context runs in it own thread.
        self.config = config
        self.store = Store()
        self.execution_context = None

    def get_service_interface(self):
        return {'service_name': self.config.SERVICE_NAME,
                'input_queue': self.config.INPUT_QUEUE_NAME,
                'output_queue': self.config.OUTPUT_QUEUE_NAME
                }

    def run(self, es_context,register=False):
        """
        for default services there is no need of registeration
        """
        self.execution_context = es_context(self.config)
        if register:
            service_info = self.get_service_interface()
            self.store.register_service(MsRegistry(**service_info))
        # db connection released as its not used further
        self.store.release_context()
        MSG_BROKER_ADDR = self.config.MESSAGE_BROKER_ADDR
        EXCHANGE_NAME = self.config.MESSAGE_BROKER_EXCHANGE
        initialize_msg_listeners(MSG_BROKER_ADDR, self.config.SERVICE_NAME, self.config.INPUT_QUEUE_NAME,
                                 self.config.OUTPUT_QUEUE_NAME, self.config.ERROR_QUEUE_NAME, EXCHANGE_NAME, self.execution_context)
