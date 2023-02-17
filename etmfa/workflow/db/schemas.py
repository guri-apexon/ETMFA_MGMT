from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, INTEGER, String, DateTime, Boolean, Index
from . import engine
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from enum import Enum 

SchemaBase = declarative_base()


class MsRegistry(SchemaBase):
   __tablename__ = 'tblMsRegistry'
   service_name = Column(String, primary_key=True)
   input_queue = Column(String)
   output_queue = Column(String)


class ServiceWorkflows(SchemaBase):
   __tablename__ = 'tblServiceWorkFlow'
   work_flow_name = Column(String, primary_key=True)
   graph = Column(JSONB)

class WorkFlowState(Enum):
   PENDING="PENDING"
   RUNNING="RUNNING"
   PAUSE="PAUSE"
   COMPLETED="COMPLETED"
   ERROR="ERROR"
   ERROR_TIMEOUT="ERROR_TIMEOUT"


class WorkFlowStatus(SchemaBase):
   __tablename__ = 'work_flow_status'
   work_flow_id = Column(String, primary_key=True)
   doc_uid = Column(String,unique=True)
   protocol_name=Column(String,nullable=False)
   work_flow_name = Column(String)
   documentFilePath=Column(String(500))
   status = Column(String, default=WorkFlowState.PENDING.value)
   all_services = Column(ARRAY(String),default=[])
   running_services = Column(ARRAY(String), default=[])  # name of service
   finished_services = Column(ARRAY(String), default=[])
   percent_complete = Column(INTEGER, default=0)
   lastUpdated = Column(DateTime(timezone=True), default=datetime.utcnow,
                        onupdate=datetime.utcnow)
   timeCreated=Column(DateTime(timezone=True),default=datetime.utcnow)
   isProcessing = Column(Boolean, default=True)
   errorCode = Column(INTEGER, default=0)
   errorReason = Column(String, default='')
   errorMessageDetails = Column(String, default='')


# keep it at end,define all schemas at top
SchemaBase.metadata.create_all(engine)
