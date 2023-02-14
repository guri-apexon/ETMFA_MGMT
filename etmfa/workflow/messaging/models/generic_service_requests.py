

from pydantic import BaseModel
from typing import Dict, List,Optional
from abc import ABC, abstractmethod


# CompositeServiceMessage is sent message to input queue of service
#ServiceInfolist in composite message tells from which services message has come
# ServiceMessage is received Message on message listener

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
  flow_name: str
  flow_id: str
  service_name:str
  error_code: int
  error_message: str
  error_message_details: Optional[str]

class LegacyErrorMessage(BaseModel):
  service_name:str
  id:str
  error_code: int
  error_message: str
  error_message_details: Optional[str]
