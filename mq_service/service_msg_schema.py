from pydantic import BaseModel
from typing import Dict, List


class ServiceInfo(BaseModel):
    service_name: str
    params: Dict


class CompositeServiceMessage(BaseModel):
    flow_name: str
    flow_id: str
    services_param: List[ServiceInfo]


class ServiceMessage(BaseModel):
    flow_name: str
    flow_id: str
    params: Dict


class ErrorMessage(BaseModel):
    service_name: str
    flow_name: str
    flow_id: str
    error_code: int
    error_message: str
    error_message_details: str


class LegacyErrorMessage(BaseModel):
    service_name: str
    id: str
    error_code: int
    error_message: str
    error_message_details: str
