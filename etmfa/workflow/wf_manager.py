import os
import time
from pydantic import BaseModel
from typing import Dict, List
from etmfa.workflow.exceptions import ReplyMsgException, SendExceptionMessages
import logging
from threading import Thread, Lock
from dataclasses import dataclass
from multiprocessing import Process
from .workflow import WorkFlow, DagParser
from .db.schemas import ServiceWorkflows, MsRegistry
from .messaging.message_handlers import ServiceMessageHandler
from .messaging import MqReceiver, MqSender, MqReqMsg, MqReplyMsg, MsqType, MqStatus
from typing import Dict, List
from .default_workflows import DEFAULT_WORKFLOWS, DEFAULT_SERVICE_FLOW_MAP, TERMINATE_NODE
from .service_handlers import GetServiceHandler, SERVICE_HANDLERS
from .messaging.models import EtmfaQueues, TERMINATE_NODE
from .db.db_utils import (create_doc_processing_status,
                          update_doc_finished_status,
                          update_doc_running_status,
                          get_pending_running_work_flows,
                          check_stale_work_flows_and_remove
                          )
from ..consts import Consts
from etmfa.workflow.loggerconfig import initialize_wf_logger, ContextFilter
from ..consts.constants import DEFAULT_WORKFLOW_NAME
from ..server.namespaces.confidence_metric import ConfidenceMatrixRunner

WF_RUN_WAIT_TIME = 3  # 3 sec


class ServiceParam(BaseModel):
    service_name: str
    param: Dict


@dataclass
class CustomWorkFlow():
    work_flow_name: str
    graph: dict


class WorkFlowMessage(BaseModel):
    work_flow_name: str
    work_flow_id: str  # unique for every run uid generated
    param: Dict


def get_db_and_broker(message_broker_exchange, message_broker_address):
    """
    Initialize database and broker instance
    """
    from etmfa.workflow import PostGresStore, StoreConfig, RabbitMqBroker, RabbitMqInfo
    StoreConfig(ms_store_name='tblMsRegistry',
                wf_store_name='tblServiceWorkFlow')
    broker_config = RabbitMqInfo(
        message_broker_exchange, message_broker_address)
    pg = PostGresStore()
    br = RabbitMqBroker(broker_config)
    return pg, br


class WorkFlowManager():

    def __init__(self, message_broker_exchange, message_broker_address, dfs_path, logger, initialize_listener=True,
                 extra_config=None):
        """
        initialize_listener: for registeration only this should be False
        """
        self.logger = logger
        self.dfs_path = dfs_path
        self.dfs_path = dfs_path
        if not extra_config:
            extra_config = {}
        self.extra_config = extra_config
        self.max_service_execution_wait_time = extra_config.get('MAX_EXECUTION_WAIT_TIME_HRS',24)

        self.store, self.broker = get_db_and_broker(
            message_broker_exchange, message_broker_address)
        self.service_message_handler = ServiceMessageHandler(
            GetServiceHandler(self.dfs_path).get_handler, self.logger)

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
        self.store.delete_all_dependancy_graph(list(DEFAULT_WORKFLOWS.keys()))
        for wf_name, graph in DEFAULT_WORKFLOWS.items():
            self.register_work_flow(wf_name, graph, True)

    def _register_default_services(self):
        etmafa_map = {
            queue_name.value: queue_name for queue_name in EtmfaQueues}
        ms_list = []
        for sr_name, _ in DEFAULT_SERVICE_FLOW_MAP.items():
            if sr_name == TERMINATE_NODE:
                continue
            sr_enum = etmafa_map[sr_name]
            ms = MsRegistry(
                service_name=sr_name, input_queue=sr_enum.request, output_queue=sr_enum.complete)
            ms_list.append(ms)
        try:
            self.store.delete_all_services(ms_list)
            self.store.register_all_services(ms_list)
        except Exception as e:
            self.logger.error("issue registering services: " + str(e))

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
        for flow_id, wf_name in running_work_flows.items():
            if wf_name not in self.work_flows:
                continue
            self.work_flows[wf_name].create_channel(flow_id)
        self.out_queue_service_map, self.service_queue_tuple_map = self._get_services_map(
            services_info)
        queues_to_monitor = list(self.out_queue_service_map.keys())
        queues_to_monitor=[ q  for q in queues_to_monitor if q]
        if self.extra_config.get('WORK_FLOW_RUNNER',False):
            queues_to_monitor.append(EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value)
        else:
            error_queue=EtmfaQueues(EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value).queue_prefix
            queues_to_monitor.append(error_queue)
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
            raise SendExceptionMessages(
                f'can not find service {curr_service_name} for output queue {out_queue_name}')

        next_services_with_msg_obj = work_flow.get_next_services(
            flow_id, curr_service_name, service_msg)
        # if there is wait for last services,next_services_with_msg_obj will be None
        if not next_services_with_msg_obj:
            if work_flow.is_work_flow_finished(flow_id):
                update_doc_finished_status(flow_id, work_flow_name)
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
        msg_key = 'flow_id' if msg_obj.get('flow_id') else 'id'
        self.logger.addFilter(ContextFilter(doc_id=msg_obj.get(msg_key, None)))
        self.logger.info(f"message received on {out_queue_name} is: {msg_obj}")
        self._process_msg(out_queue_name, msg_obj)

    def register_work_flow(self, work_flow_name, depend_graph, is_default):
        """
        store these graphs to postgres.

        """
        DagParser.validate_request(depend_graph)
        swf = ServiceWorkflows(
            work_flow_name=work_flow_name, graph=depend_graph, is_default=is_default)
        self.store.store_dependancy_graph(swf)

    def delete_work_flow(self, work_flow_name):
        self.store.delete_dependancy_graph(work_flow_name)
        
    def get_all_registered_services(self):
        return self.store.get_all_registered_services()

    def get_all_workflows_from_db(self):
        work_flow_map = {}
        sr_workflows = self.store.get_all_dependacy_graphs()
        if not sr_workflows:
            return {}
        for sr_wf in sr_workflows:
            wf_name = sr_wf.work_flow_name
            work_flow_map[wf_name] = sr_wf.graph
        return work_flow_map

    def validate_service_dependency(self, service_dependency, services):
        if len(service_dependency) == 0:
            return True, None
        else:
            for dependency in service_dependency:
                if dependency not in services:
                    return False, dependency
        return True, dependency

    def validate_dependency(self, work_flow_name, services, dependency_graph):
        dependencies = dependency_graph[work_flow_name]
        services = [service['service_name'] for service in services]
        for service_name in services:
            for service in dependencies:
                if service['service_name'] == service_name:
                    check_status, dependency = self.validate_service_dependency(service['depends'], services)
                    if not check_status:
                        return False, {"Status": "400",
                                       "Message": "Validation Error: Service {}  of workflow {} depends"
                                                  " on service {} which is not "
                                                  "selected while registering workflow {} ".format(service_name,
                                                                                                   work_flow_name,
                                                                                                   dependency,
                                                                                                   work_flow_name)}
                    break

        return True, {"Status": 200, "Message": "Dependencies Validated Successfully"}

    def validate_workflow(self, work_flow_name, workflows):
        dependency_graph = self.get_all_workflows_from_db()
        validation_status, is_valid = None, False
        if dependency_graph.get(work_flow_name) is not None:
            return False, {"Status": 400, "Message": "Duplication Error, Workflow already exists"}
        for workflow in workflows:
            is_valid, validation_status = self.validate_dependency(workflow["work_flow_name"],
                                                                   workflow['dependency_graph'],
                                                                   dependency_graph)
            if validation_status['Status'] == "400":
                return is_valid, validation_status
        return is_valid, validation_status

    def get_all_workflows(self):
        work_flow_map = {}
        sr_workflows = self.store.get_all_dependacy_graphs()
        if not sr_workflows:
            return {}
        for sr_wf in sr_workflows:
            wf_name = sr_wf.work_flow_name
            work_flow_map[wf_name] = WorkFlow(sr_wf, self.logger)
        return work_flow_map

    def add_work_flow(self, wf_info: CustomWorkFlow):
        self.work_flows[wf_info.work_flow_name] = WorkFlow(wf_info, self.logger)

    def get_work_flow(self, name):
        return self.store.get_work_flow(name)

    def wait_until_listener_ready(self):
        while (not self.broker.is_ready):
            time.sleep(3)

    @property
    def is_ready(self):
        return self.broker.is_ready

    def delete_channel_ids(self, wf_channel_ids):
        for wf_name, channel_id in wf_channel_ids:
            work_flow = self.work_flows[wf_name]
            work_flow.delete_channel(channel_id)
            self.logger.info('channel deleted for ' + str(channel_id))

    def run_work_flow(self, wf_name, flow_id, param):
        """
        Message to be sent should be adapted to requested service.
        """
        if not self.is_ready:
            raise SendExceptionMessages("work flow manager is not ready yet ")
        if not self.work_flows.get(wf_name, None):
            raise SendExceptionMessages(f"Work FLow {wf_name} is not registered ")
        work_flow = self.work_flows[wf_name]
        work_flow.create_channel(flow_id)
        update_doc_running_status(flow_id, work_flow.services_list, wf_name)
        self.logger.info(f'channel created for {wf_name}')
        for h_node in work_flow.head_nodes:
            # make this generic messages,read from mapping
            sr_name = h_node.name
            service_param = param
            input_queue_name, _ = self.service_queue_tuple_map[sr_name]
            self.logger.debug('creating start message', extra={"doc_id": flow_id})
            composite_msg = self.service_message_handler.create_start_message(
                sr_name, input_queue_name, wf_name, flow_id, service_param)
            next_service_with_comp_msg = {sr_name: composite_msg}
            self.logger.debug('creating adapted message', extra={"doc_id": flow_id})
            adapted_msg_map, skipped_services_msg_obj_map = self.service_message_handler.on_output_message_adapter(
                next_service_with_comp_msg)
            self.logger.debug(f'sending adapted message to {input_queue_name}', extra={"doc_id": flow_id})
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

    def send_msg(self, wf_name, wf_id,doc_uid, param, type: MsqType = MsqType.COMMAND.value):
        """
        type: msgtype info or command. to run workflow its COMMAND, to get info INFO
        """
        wfm = WorkFlowMessage(work_flow_name=wf_name,
                              work_flow_id=wf_id, param=param)
        data = MqReqMsg(type, wfm.dict())
        reply = self.mqs.send(data.__dict__)
        reply = MqReplyMsg(**reply)
        if reply.status != MqStatus.OK.value:
            raise ReplyMsgException(reply.msg)
        return reply.msg


class WorkFlowController(Thread):
    """
    work flow controller manages a queue
    """

    def __init__(self, message_broker_exchange, message_broker_address, dfs_path, logger, extra_config):
        self.msg_queue = []
        self.logger = logger
        self.logger.info("Controller process is " + str(os.getpid()))
        self.wfm = WorkFlowManager(
            message_broker_exchange, message_broker_address, dfs_path, logger, True, extra_config)
        self.remove_time_for_stale_workflows = extra_config['MAX_EXECUTION_WAIT_TIME_HRS']
        Thread.__init__(self)
        self.lock = Lock()
        self.daemon = True
        self.start()

    def add_msg(self, msg):
        with self.lock:
            self.logger.debug("Message added")
            wf_msg = WorkFlowMessage(**msg)
            self.msg_queue.append(wf_msg)
            self.logger.debug('doc processing status created')

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
            param = wf_msg.param
            self.wfm.run_work_flow(
                wf_msg.work_flow_name, wf_msg.work_flow_id, param)

    def on_msg(self, msg_obj):
        """
        Receive message on controller
        """
        self.logger.addFilter(ContextFilter(doc_id=msg_obj['msg'].get('work_flow_id')))
        self.logger.debug("Message received on controller")
        msg_obj = MqReqMsg(**msg_obj)
        _type, msg = msg_obj.type, msg_obj.msg
        if _type == MsqType.COMMAND.value:
            self.add_msg(msg)
        elif _type == MsqType.ADD_CUSTOM_WORKFLOW.value:
            param = msg['param']
            work_flow_list = param['work_flow_list']
            status = {}
            is_valid, status = self.wfm.validate_workflow(msg['work_flow_name'], work_flow_list)
            if not is_valid:
                return status['Message'], is_valid
            work_flow_graph, service_list = [], []
            for wfs in work_flow_list:
                depends_graph = wfs['dependency_graph']
                work_flow_graph.extend(depends_graph)
                for sr_info in depends_graph:
                    service_list.append(sr_info['service_name'])
            work_flow_graph.append({'service_name': TERMINATE_NODE, 'depends': service_list})
            self.wfm.register_work_flow(msg['work_flow_name'], work_flow_graph, False)
            self.wfm.add_work_flow(CustomWorkFlow(msg['work_flow_name'], work_flow_graph))
            return status, is_valid
        elif _type == MsqType.RUN_DEFAULT_WORKFLOW.value:
            param = msg['param']
            work_flow_list = param['work_flow_list']
            status = {}
            is_valid, status = self.wfm.validate_workflow(msg['work_flow_name'], work_flow_list)
            if not is_valid:
                return status['Message'], is_valid
            work_flow_graph, service_list = [], []
            for wfs in work_flow_list:
                depends_graph = wfs['dependency_graph']
                work_flow_graph.extend(depends_graph)
                for sr_info in depends_graph:
                    service_list.append(sr_info['service_name'])
            work_flow_graph.append({'service_name': TERMINATE_NODE, 'depends': service_list})
            self.wfm.add_work_flow(CustomWorkFlow(DEFAULT_WORKFLOW_NAME, work_flow_graph))
            return status, is_valid
        else:
            raise SendExceptionMessages(
                f"{type} is not a valid type request on controller ")
        return {}

    def run(self):
        self.wfm.wait_until_listener_ready()
        last_pending_services_check_time = time.time()
        is_start=True
        cfr=ConfidenceMatrixRunner()
        stale_work_flow_check_time_sec = max(1, self.remove_time_for_stale_workflows / 12) * 3600
        while (True):
            try:
                start_time = time.time()
                self._process_msg()
                cfr.run()
                curr_time = time.time()
                diff = curr_time - last_pending_services_check_time
                if diff > stale_work_flow_check_time_sec or is_start:
                    self.logger.info('checking stale workflows')
                    is_start=False
                    stale_ids = check_stale_work_flows_and_remove(self.remove_time_for_stale_workflows, self.logger)
                    if stale_ids:
                        self.wfm.delete_channel_ids(stale_ids)
                    last_pending_services_check_time = curr_time
                wait_time = 0.1 if curr_time - start_time > WF_RUN_WAIT_TIME else WF_RUN_WAIT_TIME
                time.sleep(wait_time)
            except Exception as e:
                self.logger.error(str(e))


class WorkFlowsHandler():
    def __init__(self, config):
        self.port = config["ZMQ_PORT"]
        self.message_broker_exchange = config["MESSAGE_BROKER_EXCHANGE"]
        self.log_stash_host = config["LOGSTASH_HOST"]
        self.log_stash_port = config["LOGSTASH_PORT"]
        self.message_broker_address = config['MESSAGE_BROKER_ADDR']
        self.dfs_path = config['DFS_UPLOAD_FOLDER']
        self.debug = config["DEBUG"]
        self.wfc = None
        self.extra_config = {'MAX_EXECUTION_WAIT_TIME_HRS': config.get('MAX_EXECUTION_WAIT_TIME_HRS', 24),
                             'WORK_FLOW_RUNNER': config.get("WORK_FLOW_RUNNER", True)
                             }
        self.logger = None

    def run_controller(self):
        self.logger = logging.getLogger(Consts.LOGGING_WF)
        # register workflow logger
        initialize_wf_logger(self.log_stash_host, self.log_stash_port)
        self.logger.info("Running workflow Runner")
        self.wfc = WorkFlowController(
            self.message_broker_exchange, self.message_broker_address, self.dfs_path, self.logger, self.extra_config)

        mqr = MqReceiver(self.port, self.wfc.on_msg)
        mqr.run()


class WorkFlowRunner(Process, WorkFlowsHandler):
    def __init__(self, config):
        """
        workflow runner runs controller in separate process
        controller reads messages
        """
        WorkFlowsHandler.__init__(self,config)
        Process.__init__(self)
        self.daemon = True

    def start_process(self):
        self.start()

    def run(self):
        self.run_controller()

class WorkFlowThreadRunner(Thread, WorkFlowsHandler):
    def __init__(self, config):
        WorkFlowsHandler.__init__(self,config)
        Thread.__init__(self)
        self.daemon = True

    def start_process(self):
        self.start()

    def run(self):
        self.run_controller()

