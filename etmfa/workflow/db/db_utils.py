from abc import abstractmethod, ABC
from datetime import datetime
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from .schemas import SchemaBase,WorkFlowStatus, WorkFlowState
from ..default_workflows import DWorkFLows
from . import SessionLocal
from sqlalchemy import or_,and_,delete
from typing import List
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.workflow.messaging.models import ProcessingStatus,LEGACY_QUEUE_NAMES


class DbMixin:
    def __init__(self):
        pass

    def read_by_id(self, table_name, id):
        with SessionLocal() as session:
            return session.query(table_name).get(id)

    def write_many(self, data_list):
        with SessionLocal() as session:
            session.add_all(data_list)
            session.commit()

    def write_unique(self, data):
        with SessionLocal() as session:
            try:
                session.add(data)
                session.commit()
            except IntegrityError as e:
                if not isinstance(e.orig, UniqueViolation):
                    raise e
                
    def delete_by_key(self,table_name,key_name,val):
        with SessionLocal() as session:
            session.query(table_name).filter(key_name==val).delete()
            session.commit()

    def delete_group_of_elms(self,table_name,key_name,elm_list):
        with SessionLocal() as session:
            session.query(table_name).filter(key_name.in_(elm_list)).delete()
            session.commit()

    def add_group_of_elms(self,elm_list):
        with SessionLocal() as session:
            for elm in elm_list:
                session.add(elm)
            session.commit()
    
    def fetch_all(self, table):
        """
        return all table info
        """
        elm_list = []
        with SessionLocal() as session:
            for elm in session.query(table).all():
                elm_list.append(elm)
        return elm_list


def get_pending_running_work_flows():
    work_flows_info = {}
    with SessionLocal() as session:
        data_list = session.query(WorkFlowStatus).filter(or_(WorkFlowStatus.status == WorkFlowState.PENDING.value,
                                                             WorkFlowStatus.status == WorkFlowState.RUNNING.value))
        for data in data_list:
            work_flows_info[data.work_flow_id] = data.work_flow_name
        session.commit()
    return work_flows_info


def check_stale_work_flows_and_remove(max_service_execution_wait_time,logger):
    stale_ids =[]
    with SessionLocal() as session:
        data_list = session.query(WorkFlowStatus).filter(or_(WorkFlowStatus.status == WorkFlowState.PENDING.value,
                                                             WorkFlowStatus.status == WorkFlowState.RUNNING.value)).all()
        curr_time=datetime.utcnow()     
        for data in data_list:
            last_time=data.lastUpdated.replace(tzinfo=None)
            diff=curr_time-last_time
            hours=round((diff.seconds)/3600,2)
            if hours>max_service_execution_wait_time:
                data.status=WorkFlowState.ERROR_TIMEOUT.value
                logger.info(f"tiemout on workflow  {data.work_flow_name} and id is {data.work_flow_id}")
                stale_ids.append((data.work_flow_name,data.work_flow_id))
            warning_time=max(1,int(max_service_execution_wait_time/3))
            if hours>warning_time:
                logger.warning(f"work flow {data.work_flow_id} not updated since {hours} hours")
        session.commit()
    return stale_ids


def create_doc_processing_status(work_flow_id, doc_uid, work_flow_name, doc_file_path):
    status = WorkFlowStatus(
        work_flow_id=work_flow_id, doc_uid=doc_uid, work_flow_name=work_flow_name, documentFilePath=doc_file_path)
    with SessionLocal() as session:
        try:
            session.add(status)
            session.commit()
        except Exception as e:
            if not isinstance(e.orig, UniqueViolation):
                raise e
            return False
    return True


def update_doc_running_status(id, services_list,work_flow_name):
    with SessionLocal() as session:
        data = session.query(WorkFlowStatus).get(id)
        data.status = WorkFlowState.RUNNING.value
        data.all_services = services_list
        session.commit()


def get_work_flow_name_by_id(id):
    with SessionLocal() as session:
        data = session.query(WorkFlowStatus).get(id)
        return data.work_flow_name

def get_work_flow_info_by_id(id):
    if not id:
        raise Exception("cant fetch information for None id ")
    data={}
    with SessionLocal() as session:
        row = session.query(WorkFlowStatus).get(id)
        for column in row.__table__.columns:
            data[column.name] = (getattr(row, column.name))
    return data
    
def get_session_obj():
    return SessionLocal()

                                                                                                                                                                                               
def update_doc_processing_status(id: str, service_name, service_added,work_flow_name,count=1):
    """
    count: few case mulitple parallel services are invoked
    """
    with SessionLocal() as session:
        data = session.query(WorkFlowStatus).get(id)
        running_services = data.running_services.copy()
        finished_services = data.finished_services.copy()
        all_services=data.all_services.copy()
        if service_added:
            for _ in range(count):
                running_services.append(service_name)
            if count>1:
                for _ in range(1,count):
                    all_services.append(service_name)              
        else:
            if service_name in running_services:
                running_services.remove(service_name)
                finished_services.append(service_name)
        data.running_services = list(running_services)
        data.finished_services = list(finished_services)
        data.all_services=all_services
        percentage = int((len(set(data.finished_services))/len(set(all_services)))*100)
        data.percent_complete = percentage
        #older flow compatibility
        if work_flow_name==DWorkFLows.FULL_FLOW.value:
            data = session.query(PDProtocolMetadata).get(id)
            if service_name in LEGACY_QUEUE_NAMES: 
                post_fix='STARTED' if service_added else  "COMPLETED"            
                data.status = service_name.upper()+'_'+post_fix
            data.percentComplete=str(percentage)
        session.commit()


def update_doc_finished_status(id,work_flow_name):
    with SessionLocal() as session:
        data = session.query(WorkFlowStatus).get(id)
        data.status = WorkFlowState.COMPLETED.value
        data.percent_complete=int(ProcessingStatus.PROCESS_COMPLETED.value)
        data.isProcessing = False
        if work_flow_name==DWorkFLows.FULL_FLOW.value:
            data = session.query(PDProtocolMetadata).get(id)
            data.percentComplete =str(ProcessingStatus.PROCESS_COMPLETED.value)
            data.status = ProcessingStatus.PROCESS_COMPLETED.name
            data.isProcessing=False
        session.commit()
    
        

def update_doc_error_status(id,work_flow_name, error_code, error_reason, error_details):
    with SessionLocal() as session:
        data = session.query(WorkFlowStatus).get(id)
        data.errorCode = error_code
        data.errorReason = error_reason
        data.errorMessageDetails = error_details
        data.isProcessing = False
        data.status = WorkFlowState.ERROR.value
        data.running_services = []
        if work_flow_name==DWorkFLows.FULL_FLOW.value:
            data = session.query(PDProtocolMetadata).get(id)
            data.errorReason =error_reason
            data.errorCode=error_code
            data.errorDetails=error_details
            data.status = WorkFlowState.ERROR.value
            data.isProcessing=False
        session.commit()
