from dataclasses import dataclass, field
from threading import Lock
from typing import List, Dict, List, Set,Optional
from pydantic import BaseModel, ValidationError
from .db.schemas import ServiceWorkflows
import copy
from .messaging.models import ServiceInfo, CompositeServiceMessage,TERMINATE_NODE


class NodeInfoModel(BaseModel):
    service_name: str
    depends: List[str]
    count:Optional[float] = 1


@dataclass
class Node:
    name: str
    count: int=1
    next: List["Node"] = field(default_factory=list)
    prev: List["Node"] = field(default_factory=list)


class DAG:
    def __init__(self):
        self.node_dict: Dict[Node] = {}

    def add_node(self, node):
        curr_node = self.node_dict.get(
            node.service_name, Node(node.service_name,node.count))
        prev_nodes = []
        for service_name in node.depends:
            if not service_name.strip():
                continue
            prev_node = self.node_dict.get(service_name, Node(service_name))
            prev_node.next.append(curr_node)
            prev_nodes.append(prev_node)
            self.node_dict[service_name] = prev_node
        curr_node.prev.extend(prev_nodes)
        self.node_dict[curr_node.name] = curr_node

    def parse(self, nodes_info):
        for n_info in nodes_info:
            self.add_node(n_info)
        return self.node_dict

    def get_head_tail_nodes(self):
        """
        node can be both head and tail nodes
        """
        head_nodes, tail_nodes = [], []
        for nk, nv in self.node_dict.items():
            if not nv.prev:
                head_nodes.append(nv)
            if not nv.next:
                tail_nodes.append(nv)
        return head_nodes, tail_nodes


class DagParser():
    def __init__(self):
        self.dag = DAG()

    @staticmethod
    def validate_request(request) -> List[NodeInfoModel]:
        info_list = []
        for data in request:
            try:
                info = NodeInfoModel(**data)
                info_list.append(info)
            except Exception as e:
                raise (ValidationError)
        return info_list

    def build_dag(self, nodes_info: List[NodeInfoModel]) -> Node:
        return self.dag.parse(nodes_info)

    def get_node(self, name):
        return self.dag.node_dict[name]

    def get_head_tail_nodes(self):
        return self.dag.get_head_tail_nodes()

    def parse(self, request: List[NodeInfoModel]) -> List[Node]:
        parsed_request = DagParser.validate_request(request)
        return self.build_dag(parsed_request)


class Channel():
    def __init__(self, flow_name, flow_id, node_graph):
        self.flow_name = flow_name
        self.flow_id = flow_id
        self.node_graph = copy.deepcopy(node_graph)
        self.pending_services: Set[str] = set([])
        self.executed_services: Set[str] = set([])
        self.services_msg: Dict[str, Dict] = {}

    def _is_dependency_resolved(self, service_name):
        curr_node = self.node_graph[service_name]
        dependent_services_name = [nn.name for nn in curr_node.prev]
        if not set(dependent_services_name).difference(self.executed_services):
            return True
        return False

    def _get_previous_services_param(self, curr_service_name) -> List[Dict]:
        prev_services_param = [ServiceInfo(service_name=nn.name, params=self.services_msg[nn.name])
                               for nn in self.node_graph[curr_service_name].prev]
        return prev_services_param

    def add_message(self, service_name, msg_obj):
        self.services_msg[service_name] = msg_obj

    def is_service_all_instance_executed(self,service_name):
        curr_node = self.node_graph[service_name]
        if curr_node.count==1:
            return True
        curr_node.count-=1     
        return False

    def dynamic_instance_creation_check_update(self,service_msg_map):
        for service_name,msg_obj in service_msg_map.items():
            if isinstance(msg_obj,list):
                curr_node = self.node_graph[service_name]
                curr_node.count=len(msg_obj)

    def get_next_services_to_run(self, service_name):
        """
        nodes for which all dependencies are resolved will be executed
        """

        curr_node = self.node_graph[service_name]
        self.executed_services.add(service_name)
        next_node_names = [nn.name for nn in curr_node.next]
        # add nodes to pending services and check if any of those can be executed next
        self.pending_services.update(set(next_node_names))
        next_services_to_run = []
        for nx_sr_name in self.pending_services:
            if self._is_dependency_resolved(nx_sr_name):
                next_services_to_run.append(nx_sr_name)
        # remove items from next input nodes
        for nx_sr in next_services_to_run:
            self.pending_services.remove(nx_sr)
            if nx_sr==TERMINATE_NODE:
                next_services_to_run=[]
        #This is the last dummy node terminate all

        return next_services_to_run

    def get_services_composite_message(self, next_services_to_run) -> Dict[str, CompositeServiceMessage]:
        """
        every service will have a different message object to run
        """
        services_composite_msg = {}
        for sr_name in next_services_to_run:
            services_param = self._get_previous_services_param(sr_name)
            msg = CompositeServiceMessage(
                flow_name=self.flow_name, flow_id=self.flow_id, services_param=services_param)
            services_composite_msg[sr_name] = msg
        return services_composite_msg


class WorkFlow():
    def __init__(self, work_flow_info: ServiceWorkflows, logger):
        self.logger = logger
        self.work_flow_name = work_flow_info.work_flow_name
        self.head_nodes, self.tail_nodes = [], []
        self.node_graph = self._parse_dependancy_graph(work_flow_info.graph)
        self._services_list = list(self.node_graph.keys())
        self.channels: Dict[str, Channel] = {}
        self.lock = Lock()

    @property
    def services_list(self):
        return self._services_list

    def get_channel(self,flow_id):
        with self.lock:
            return self.channels[flow_id]

    def _parse_dependancy_graph(self, dep_graph):
        dp = DagParser()
        graph = dp.parse(dep_graph)
        self.head_nodes, self.tail_nodes = dp.get_head_tail_nodes()
        return graph

    def create_channel(self, flow_id):
        with self.lock:
            if flow_id in self.channels:
                raise Exception(f'id {flow_id} already being processed  ')
            self.channels[flow_id] = Channel(
                self.work_flow_name, flow_id, self.node_graph)
            self.logger.info(f'{flow_id} is added to channel')

    def delete_channel(self, flow_id):
        """"
        if all nodes in workflow executed delete the channel..
        """
        with self.lock:
            if flow_id in self.channels:
                del self.channels[flow_id]

    def is_work_flow_finished(self, flow_id):
       return True if flow_id not in self.channels else False

    def get_next_services(self, flow_id, service_name, msg_obj) -> Dict[str, CompositeServiceMessage]:
        """
        get next services which can be executed.
        only services whose all dependencies resloved can be run
        """
        channel = self.channels.get(flow_id, None)
        if not channel:
            raise Exception(
                'channel is not created yet ,might be pending message received')
        channel.add_message(service_name, msg_obj.params)
        next_services = channel.get_next_services_to_run(service_name)
        #add end node info here and break
        if not next_services and not channel.pending_services:
            if channel.is_service_all_instance_executed(service_name):
                self.delete_channel(flow_id)
                self.logger.info(
                    f'deleting workflow channel {flow_id} as all done')
            return
        services_msg_obj = channel.get_services_composite_message(
            next_services)

        return services_msg_obj
