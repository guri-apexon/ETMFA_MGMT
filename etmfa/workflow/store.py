
from abc import ABC, abstractmethod
from typing import Type, TypeVar, List
from dataclasses import dataclass
from .workflow import WorkFlow
from .db.db_utils import DbMixin
from .db.schemas import ServiceWorkflows, MsRegistry


class WorkFlowStore(ABC):

    @abstractmethod
    def get_work_flow(self, name):
        pass

    @abstractmethod
    def get_all_dependacy_graphs(self) -> List[ServiceWorkflows]:
        pass

    @abstractmethod
    def store_dependancy_graph(self, name, data):
        pass

    @abstractmethod
    def get_all_registered_services(self):
        pass

    @abstractmethod
    def register_service(self, data: MsRegistry):
        pass


@dataclass
class StoreConfig:
    ms_store_name: str
    wf_store_name: str


class LocalStoreConfig(StoreConfig):
    path: str


# only StoreConfig and its derived types
TConfig = TypeVar("TConfig", bound="StoreConfig")


class PostGresStore(WorkFlowStore, DbMixin):
    """
    local store is only for testing.
    """

    def get_work_flow(self, wf_name: str) -> WorkFlow:
        return self.read_by_id(wf_name)

    def store_dependancy_graph(self,depend_graph_info) -> None:
        self.write_unique(depend_graph_info)

    def delete_all_dependancy_graph(self,wf_list:List):
        self.delete_group_of_elms(ServiceWorkflows,ServiceWorkflows.work_flow_name,wf_list)

    def get_all_dependacy_graphs(self) -> List[ServiceWorkflows]:
        return self.fetch_all(ServiceWorkflows)

    def get_all_registered_services(self) -> List[MsRegistry]:
        """
        fetch all 
        """
        return self.fetch_all(MsRegistry)
    
    def delete_all_services(self,data_list:List):
        service_names=[data.service_name  for data in data_list]
        self.delete_group_of_elms(MsRegistry,MsRegistry.service_name,service_names)

    def register_all_services(self,data_list):
        self.add_group_of_elms(data_list)
        
    def register_service(self, data: MsRegistry):
        self.delete_by_key(MsRegistry,MsRegistry.service_name,data.service_name)
        self.write_unique(data)
