from abc import abstractmethod, ABC
import datetime
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from .schemas import SchemaBase, WorkFlowStatus, WorkFlowState
from ..default_workflows import DWorkFLows
from . import SessionLocal
from sqlalchemy import or_, and_, delete, text
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.workflow.messaging.models import ProcessingStatus, LEGACY_QUEUE_NAMES
from ..exceptions import SendExceptionMessages
from ...db import db_context
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.workflow.db import engine
from etmfa.workflow.db.schemas import ServiceWorkflows
from sqlalchemy import or_, and_, case, func, literal
from etmfa.consts.constants import EXCLUDED_WF, WORKFLOW_ORDER


class DbMixin:

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

    def delete_by_key(self, table_name, key_name, val):
        with SessionLocal() as session:
            session.query(table_name).filter(key_name == val).delete()
            session.commit()

    def delete_group_of_elms(self, table_name, key_name, elm_list):
        with SessionLocal() as session:
            session.query(table_name).filter(key_name.in_(elm_list)).delete()
            session.commit()

    def add_group_of_elms(self, elm_list):
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


def check_stale_work_flows_and_remove(max_service_execution_wait_time, logger):
    stale_ids = []
    with SessionLocal() as session:
        data_list = session.query(WorkFlowStatus).filter(or_(WorkFlowStatus.status == WorkFlowState.PENDING.value,
                                                             WorkFlowStatus.status == WorkFlowState.RUNNING.value)).all()
        curr_time = datetime.datetime.utcnow()
        for data in data_list:
            last_time = data.lastUpdated.replace(tzinfo=None)
            diff = curr_time - last_time
            hours = round((diff.seconds) / 3600, 2)
            if hours > max_service_execution_wait_time:
                data.status = WorkFlowState.ERROR_TIMEOUT.value
                logger.info(f"tiemout on workflow  {data.work_flow_name} and id is {data.work_flow_id}")
                stale_ids.append((data.work_flow_name, data.work_flow_id))
            warning_time = max(1, int(max_service_execution_wait_time / 3))
            if hours > warning_time:
                logger.warning(f"work flow {data.work_flow_id} not updated since {hours} hours")
        session.commit()
    return stale_ids


def create_doc_processing_status(work_flow_id, doc_id, doc_uid, work_flow_name, doc_file_path, protocol_name):
    status = WorkFlowStatus(
        work_flow_id=work_flow_id, doc_id=doc_id, doc_uid=doc_uid, work_flow_name=work_flow_name,
        protocol_name=protocol_name,
        documentFilePath=doc_file_path)
    with SessionLocal() as session:
        try:
            session.add(status)
            session.commit()
        except Exception as e:
            if not isinstance(e.orig, UniqueViolation):
                raise e
            return False
    return True


def update_doc_running_status(id, services_list, work_flow_name):
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
        raise SendExceptionMessages("cant fetch information for None id ")
    data = {}
    with SessionLocal() as session:
        row = session.query(WorkFlowStatus).get(id)
        for column in row.__table__.columns:
            data[column.name] = (getattr(row, column.name))
    return data


def get_session_obj():
    return SessionLocal()


def _update_running_finished_services(data, service_name, service_added, count):
    running_services = data.running_services.copy()
    finished_services = data.finished_services.copy()
    all_services = data.all_services.copy()
    if service_added:
        for _ in range(count):
            running_services.append(service_name)
        if count > 1:
            for _ in range(1, count):
                all_services.append(service_name)
    else:
        if service_name in running_services:
            running_services.remove(service_name)
            finished_services.append(service_name)
    return all_services, running_services, finished_services


def update_doc_processing_status(id: str, service_name, service_added, work_flow_name, count=1):
    """
    count: few case mulitple parallel services are invoked
    """
    with SessionLocal() as session:
        data = session.query(WorkFlowStatus).get(id)
        all_services, running_services, finished_services = _update_running_finished_services(
            data, service_name, service_added, count)
        data.running_services = list(running_services)
        data.finished_services = list(finished_services)
        data.all_services = all_services
        percentage = int((len(set(data.finished_services)) / len(set(all_services))) * 100)
        data.percent_complete = percentage
        # older flow compatibility
        if work_flow_name == DWorkFLows.FULL_FLOW.value:
            data = session.query(PDProtocolMetadata).get(id)
            if service_name in LEGACY_QUEUE_NAMES:
                post_fix = 'STARTED' if service_added else "COMPLETED"
                data.status = service_name.upper() + '_' + post_fix
            data.percentComplete = str(percentage)
        session.commit()


def update_doc_finished_status(id, work_flow_name):
    with SessionLocal() as session:
        data = session.query(WorkFlowStatus).get(id)
        data.status = WorkFlowState.COMPLETED.value
        data.percent_complete = int(ProcessingStatus.PROCESS_COMPLETED.value)
        all_services = list(set(data.all_services.copy()))
        data.finished_services = all_services
        data.all_services = all_services
        data.running_services = []
        data.isProcessing = False
        if work_flow_name == DWorkFLows.FULL_FLOW.value:
            data = session.query(PDProtocolMetadata).get(id)
            data.percentComplete = str(ProcessingStatus.PROCESS_COMPLETED.value)
            data.status = ProcessingStatus.PROCESS_COMPLETED.name
            data.isProcessing = False
        session.commit()


def update_doc_error_status(id, work_flow_name, error_code, error_reason, error_details):
    with SessionLocal() as session:
        data = session.query(WorkFlowStatus).get(id)
        data.errorCode = error_code
        data.errorReason = error_reason
        data.errorMessageDetails = error_details
        data.isProcessing = False
        data.status = WorkFlowState.ERROR.value
        data.running_services = []
        if work_flow_name == DWorkFLows.FULL_FLOW.value:
            data = session.query(PDProtocolMetadata).get(id)
            data.errorReason = error_reason
            data.errorCode = error_code
            data.errorDetails = error_details
            data.status = WorkFlowState.ERROR.value
            data.isProcessing = False
        session.commit()


def segregate_workflows(workflows):
    default_workflows = {}
    custom_workflows = {}
    for workflow in workflows:
        is_default = workflow.get('is_default')
        workflow_name = workflow.get('work_flow_name')
        if is_default:
            if workflow_name not in EXCLUDED_WF:
                default_workflows[workflow_name] = workflow['graph']
        else:
            if workflow_name not in EXCLUDED_WF:
                custom_workflows[workflow_name] = workflow['graph']
    return default_workflows, custom_workflows


def get_all_workflows_from_db():
    """This function fetches all workflows of db from workflow status table"""
    session = db_context.session()
    obj = session.query(ServiceWorkflows.work_flow_name, ServiceWorkflows.graph,
                        ServiceWorkflows.is_default).all()
    workflows = [i._asdict() for i in obj]
    return segregate_workflows(workflows)


def get_wf_by_doc_id(doc_id, days=None, wf_num=None):
    """This function queries db to fetch records based on doc_id , number of days & number of work flows"""
    session = db_context.session()
    wfs = session.query(WorkFlowStatus.doc_id.label('id'), WorkFlowStatus.work_flow_id.label('wfId'),
                        WorkFlowStatus.status.label('wfStatus'),
                        WorkFlowStatus.all_services.label('wfAllServices'),
                        WorkFlowStatus.running_services.label('wfRunningServices'),
                        WorkFlowStatus.work_flow_name.label('wfName'),
                        WorkFlowStatus.errorMessageDetails.label('wfErrorMessageDetails'),
                        WorkFlowStatus.finished_services.label('wfFinishedServices'),
                        WorkFlowStatus.percent_complete.label('wfPercentComplete'),
                        func.to_char(WorkFlowStatus.timeCreated, 'DD-Mon-YYYY').label('timeCreated')). \
        filter(WorkFlowStatus.doc_id == doc_id).order_by(
        WorkFlowStatus.timeCreated.desc())
    if days:
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=int(days))
        wfs = wfs.filter(WorkFlowStatus.timeCreated >= start_date,
                         WorkFlowStatus.timeCreated <=
                         end_date)
    if wf_num:
        wfs = wfs.limit(wf_num)
    session.close()
    all_wf_data = [wf._asdict() for wf in wfs.all()]
    sorted_all_wf_data = sort_all_services(all_wf_data)
    return sorted_all_wf_data


def sort_all_services(all_wf_data):
    """This Function is used to sort all the workflows in correct sequence of execution"""
    sorted_all_wf_data = []
    for wf_data in all_wf_data:
        sorted_wf_data = []
        for service in WORKFLOW_ORDER:
            if service in wf_data['wfAllServices']:
                sorted_wf_data.append(service)
        wf_data['wfAllServices'] = sorted_wf_data
        sorted_all_wf_data.append(wf_data)
    return sorted_all_wf_data
