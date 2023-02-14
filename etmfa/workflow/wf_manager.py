import os
import time
from pydantic import BaseModel
from typing import Dict, List
from . import Consts
import logging
from threading import Thread, Lock
from dataclasses import dataclass
from multiprocessing import Process
from .workflow import WorkFlow, DagParser
from .db.schemas import ServiceWorkflows, MsRegistry
from .messaging.message_handlers import ServiceMessageHandler
from .messaging import MqReceiver, MqSender, MqReqMsg, MqReplyMsg, MsqType, MqStatus
from typing import Dict, List
from .default_workflows import DEFAULT_WORKFLOWS, DEFAULT_SERVICE_FLOW_MAP
from .service_handlers import GetServiceHandler, SERVICE_HANDLERS
from .messaging.models import EtmfaQueues, TERMINATE_NODE
from .db.db_utils import (create_doc_processing_status,
                          update_doc_finished_status,
                          update_doc_running_status,
                          get_pending_running_work_flows
                          )
from ..server.loggingconfig import initialize_logger


WF_RUN_WAIT_TIME = 2  # 2 sec


class ServiceParam(BaseModel):
    service_name: str
    param: Dict


class WorkFlowMessage(BaseModel):
    work_flow_name: str
    work_flow_id: str  # unique for every run uid generated
    doc_uid: str  # unique w.r.t document
    param: Dict


def get_db_and_broker(message_broker_exchange, message_broker_address):
    """
    Initialize database and broker instance
    """
    from etmfa.workflow import PostGresStore, StoreConfig, RabbitMqBroker, RabbitMqInfo
    sc = StoreConfig(ms_store_name='tblMsRegistry',
                     wf_store_name='tblServiceWorkFlow')
    broker_config = RabbitMqInfo(
        message_broker_exchange, message_broker_address)
    pg = PostGresStore()
    br = RabbitMqBroker(broker_config)
    return pg, br


class WorkFlowManager():

    def __init__(self, message_broker_exchange, message_broker_address, dfs_path, logger, initialize_listener=True):
        """
        initialize_listener: for registeration only this should be False
        """
        self.logger = logger
        self.dfs_path = dfs_path
        self.dfs_path = dfs_path
        self.store, self.broker = get_db_and_broker(
            message_broker_exchange, message_broker_address)
        self.service_message_handler = ServiceMessageHandler(
            GetServiceHandler(self.dfs_path).get_handler)

        self.work_flows: Dict[str, WorkFlow] = {}
        if initialize_listener:
            self.on_init()

    def register_service_message_handler(self, service_name, handler):
        self.service_message_handler.register_msg_service_handler(
            service_name, handler)

    def get_running_work_flows(self):
        running_flows = []
        for wf_name, wf in self.work_flows.items():
            for flow_name, _ in wf.channels.items():
                running_flows.append(flow_name)
        return running_flows

    def clear_running_work_flows(self):
        for wf_name, wf in self.work_flows.items():
            wf.channels = {}

    def _get_services_map(self, services_info: List[MsRegistry]):
        out_queue_service_map, service_queue_tuple_map = {}, {}
        for sr_info in services_info:
            input_queue, output_queue, sr_name = sr_info.input_queue, sr_info.output_queue, sr_info.service_name
            out_queue_service_map[output_queue] = sr_name
            service_queue_tuple_map[sr_name] = (input_queue, output_queue)
        return out_queue_service_map, service_queue_tuple_map

    def _register_default_workflows(self):
        """
        register all default workflows
        """
        for wf_name, graph in DEFAULT_WORKFLOWS.items():
            self.register_work_flow(wf_name, graph)

    def _register_default_services(self):
        etmafa_map = {
            queue_name.value: queue_name for queue_name in EtmfaQueues}

        for sr_name, _ in DEFAULT_SERVICE_FLOW_MAP.items():
            if sr_name == TERMINATE_NODE:
                continue
            sr_enum = etmafa_map[sr_name]
            ms = MsRegistry(
                service_name=sr_name, input_queue=sr_enum.request, output_queue=sr_enum.complete)
            self.store.register_service(ms)

    def on_init(self):
        """
        read all MS from registry
        read all registered workflows
        """
        self._register_default_services()
        self._register_default_workflows()
        services_info = self.get_all_registered_services()
        self.broker.add_listener(self.on_msg)
        self.work_flows = self.get_all_workflows()
        running_work_flows = get_pending_running_work_flows()
        for wf_name, flow_id in running_work_flows.items():
            if wf_name not in self.work_flows:
                continue
            self.work_flows[wf_name].create_channel(flow_id)
        self.out_queue_service_map, self.service_queue_tuple_map = self._get_services_map(
            services_info)
        queues_to_monitor = list(self.out_queue_service_map.keys())

        queues_to_monitor.append(EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value)
        self.logger.info(f"Monitoring queues :{queues_to_monitor}")
        self.broker.add_queues_to_monitor(queues_to_monitor)

    def _handle_skipped_services(self, skipped_services_msg_obj_map):
        """
        call on_msg to pass through this call ,so workflow executes next items
        """
        for sr_name, msg_obj in skipped_services_msg_obj_map.items():
            output_queue_name = self.service_queue_tuple_map[sr_name][1]
            self.on_msg(output_queue_name, msg_obj)

    def _process_msg(self, out_queue_name, msg_obj):
        curr_service_name = self.out_queue_service_map.get(
            out_queue_name, None)
        if not curr_service_name:
            curr_service_name = EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value
        msg_obj = self.service_message_handler.on_input_message_adapter(
            msg_obj, curr_service_name)
        meta_info = {}  # additional info w.r.t stage in pipeline etc.
        service_msg = self.service_message_handler.on_msg(
            msg_obj, curr_service_name, meta_info)

        if curr_service_name == EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value:
            work_flow = self.work_flows[service_msg.flow_name]
            work_flow.delete_channel(service_msg.flow_id)
            self.logger.info(f'channel is deleted {service_msg.flow_id}')
            return
        work_flow_name = service_msg.flow_name
        flow_id = service_msg.flow_id
        work_flow = self.work_flows[work_flow_name]

        if not curr_service_name:
            raise Exception(
                f'can not find service {curr_service_name} for output queue {out_queue_name}')

        next_services_with_msg_obj = work_flow.get_next_services(
            flow_id, curr_service_name, service_msg)
        # if there is wait for last services,next_services_with_msg_obj will be None
        if not next_services_with_msg_obj:
            if work_flow.is_work_flow_finished(flow_id):
                update_doc_finished_status(flow_id,work_flow_name)
            return
        next_services_input_queue = {
            sr: self.service_queue_tuple_map[sr][0] for sr in next_services_with_msg_obj.keys()}
        # add output adapter
        next_services_with_msg_obj, skipped_services_msg_obj_map = self.service_message_handler.on_output_message_adapter(
            next_services_with_msg_obj)
        work_flow.get_channel(flow_id).dynamic_instance_creation_check_update(
            next_services_with_msg_obj)
        self.broker.send_msg_list(
            next_services_with_msg_obj, next_services_input_queue)
        self._handle_skipped_services(skipped_services_msg_obj_map)

    def on_msg(self, out_queue_name, msg_obj):
        """
        callback handler from broker.
        out_queue_name: queue where message needs to be sent
        handle message w.r.t queue in MessageHandler
        check which services can run next based on dependancy graph
        message from broker comes here ,as we listening for output queues this is output queue
        get workflow to which it belongs
        """
        self.logger.info("message received is "+str(msg_obj))
        self._process_msg(out_queue_name, msg_obj)

    def register_work_flow(self, work_flow_name, depend_graph):
        """
        store these graphs to postgres.

        """
        DagParser.validate_request(depend_graph)
        swf = ServiceWorkflows(
            work_flow_name=work_flow_name, graph=depend_graph)
        self.store.store_dependancy_graph(swf)

    def get_all_registered_services(self):
        return self.store.get_all_registered_services()

    def get_all_workflows(self):
        work_flow_map = {}
        sr_workflows = self.store.get_all_dependacy_graphs()
        if not sr_workflows:
            return {}
        for sr_wf in sr_workflows:
            wf_name = sr_wf.work_flow_name
            work_flow_map[wf_name] = WorkFlow(sr_wf, self.logger)
        return work_flow_map

    def get_work_flow(self, name):
        return self.store.get_work_flow(name)

    def wait_until_listener_ready(self):
        while (not self.broker.is_ready):
            time.sleep(3)

    @ property
    def is_ready(self):
        return self.broker.is_ready

    def run_work_flow(self, wf_name, flow_id, param):
        """
        Message to be sent should be adapted to requested service.
        """
        if not self.is_ready:
            raise Exception("work flow manager is not ready yet ")
        if not self.work_flows.get(wf_name, None):
            raise Exception(f"Work FLow {wf_name} is not registered ")
        work_flow = self.work_flows[wf_name]
        work_flow.create_channel(flow_id)
        update_doc_running_status(flow_id,work_flow.services_list,wf_name)
        self.logger.info(f'channel created for {wf_name}')
        for h_node in work_flow.head_nodes:
            # make this generic messages,read from mapping
            sr_name = h_node.name
            service_param = param
            input_queue_name, _ = self.service_queue_tuple_map[sr_name]
            self.logger.debug('creating start message')
            composite_msg = self.service_message_handler.create_start_message(
                sr_name, input_queue_name, wf_name, flow_id, service_param)
            next_service_with_comp_msg = {sr_name: composite_msg}
            self.logger.debug('creating adapted message')
            adapted_msg_map, skipped_services_msg_obj_map = self.service_message_handler.on_output_message_adapter(
                next_service_with_comp_msg)
            self.logger.debug('sending adapted message to ', input_queue_name)
            work_flow.get_channel(
                flow_id).dynamic_instance_creation_check_update(adapted_msg_map)
            self.broker.send_msg(adapted_msg_map[sr_name], input_queue_name)

            self._handle_skipped_services(skipped_services_msg_obj_map)


class WorkFlowClient():
    def __new__(cls, port=None, logger=None):
        if not hasattr(cls, 'instance'):
            cls.instance = super(WorkFlowClient, cls).__new__(cls)
            cls.instance.initialize(port, logger)
        return cls.instance
    
    def initialize(self, port: int = None, logger=None):
        self.mqs = MqSender(str(port))
        self.logger = logger

    def send_msg(self, wf_name, wf_id, doc_uid, param, type: MsqType = MsqType.COMMAND.value):
        """
        type: msgtype info or command. to run workflow its COMMAND, to get info INFO
        """

        wfm = WorkFlowMessage(work_flow_name=wf_name,
                              work_flow_id=wf_id, doc_uid=doc_uid, param=param)
        data = MqReqMsg(type, wfm.dict())
        reply = self.mqs.send(data.__dict__)
        reply = MqReplyMsg(**reply)
        if reply.status != MqStatus.OK.value:
            raise Exception(reply.msg)
        return reply.msg


class WorkFlowController(Thread):
    """
    work flow controller manages a queue
    """

    def __init__(self, message_broker_exchange, message_broker_address, dfs_path, logger):
        self.msg_queue = []
        self.logger = logger
        self.logger.info("Controller process is "+str(os.getpid()))
        self.wfm = WorkFlowManager(
            message_broker_exchange, message_broker_address, dfs_path, logger, True)
        Thread.__init__(self)
        self.lock = Lock()
        self.daemon = True
        self.start()

    def add_msg(self, msg):
        with self.lock:
            self.logger.debug("Message added :", msg)
            wf_msg = WorkFlowMessage(**msg)
            self.msg_queue.append(wf_msg)
            self.logger.debug('doc pressing status created')

    def get_msg(self):
        with self.lock:
            if len(self.msg_queue) != 0:
                return self.msg_queue.pop(0)
            return None

    def _process_msg(self):
        """
        process all the messages from queue ,when no message in queue break loop
        """
        while (True):
            wf_msg = self.get_msg()
            if not wf_msg:
                break
            self.logger.debug('processing msg')
            param = wf_msg.param
            self.logger.debug('running workflow')
            self.wfm.run_work_flow(
                wf_msg.work_flow_name, wf_msg.work_flow_id, param)

    def on_msg(self, msg_obj):
        """
        Receive message on controller
        """
        self.logger.debug("Message received on controller :", msg_obj)
        msg_obj = MqReqMsg(**msg_obj)
        type, msg = msg_obj.type, msg_obj.msg
        if type == MsqType.COMMAND.value:
            self.add_msg(msg)
        elif type == MsqType.INFO:
            raise Exception(f"{type} is not implemented yet in controller ")
        else:
            raise Exception(
                f"{type} is not a valid type request on controller ")
        return {}

    def run(self):
        self.wfm.wait_until_listener_ready()
        while (True):
            try:
                self._process_msg()
                time.sleep(WF_RUN_WAIT_TIME)
            except Exception as e:
                self.logger.error(str(e))


class WorkFlowRunner(Process):
    def __init__(self, config):
        """
        workflow runner runs controller in separate process
        controller reads messages
        """
        self.port = config["ZMQ_PORT"]
        self.message_broker_exchange = config["MESSAGE_BROKER_EXCHANGE"]
        self.log_stash_host = config["LOGSTASH_HOST"]
        self.log_stash_port = config["LOGSTASH_PORT"]
        self.message_broker_address=config['MESSAGE_BROKER_ADDR']
        self.dfs_path = config['DFS_UPLOAD_FOLDER']
        self.debug = config["DEBUG"]
        self.logger = None
        Process.__init__(self)
        self.daemon = True

    def start_process(self):
        self.start()

    def run(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(Consts.LOGGING_WF)
        initialize_logger(self.log_stash_host, self.log_stash_port)
        self.logger.info("Running workflow Runner")
        wfc = WorkFlowController(
            self.message_broker_exchange, self.message_broker_address, self.dfs_path, self.logger)

        mqr = MqReceiver(self.port, wfc.on_msg)
        mqr.run()
