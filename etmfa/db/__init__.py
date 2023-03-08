import ast
import datetime
import json
import logging
import os
import uuid
from datetime import datetime
from etmfa.db.db import db_context
from etmfa.db import utils, generate_email, config
from etmfa.consts import Consts as consts
from etmfa.db.models.documentcompare import Documentcompare
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.db.models.pd_protocol_data import Protocoldata
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_protocol_qc_summary_data import PDProtocolQCSummaryData
from etmfa.db.models.pd_protocol_qcdata import Protocolqcdata
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.error import ErrorCodes, ManagementException
from etmfa.workflow.messaging.models.processing_status import (FeedbackStatus,
                                                               ProcessingStatus, QcStatus)
from etmfa.db.models.work_flow_status import WorkFlowStatus, WorkFlowState
from pathlib import Path
from flask import g, abort
from sqlalchemy import and_, func,or_
from sqlalchemy.sql import text
from typing import List, Dict
from etmfa.workflow.messaging.models.queue_names import EtmfaQueues
from etmfa.workflow.default_workflows import DWorkFLows
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

# added for pd 2.0
from etmfa.db.models.pd_iqvassessmentvisitrecord_db import IqvassessmentvisitrecordDb, IqvassessmentvisitrecordDbMapper
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata, MetaDataTableHelper


logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"
NO_RESOURCE_FOUND = "No document resource is found for requested input(s): {}"
NO_COMPARE_RESOURCE_FOUND = "No document resource is found for requested input(s): {}, {}"
ERROR_PROCESSING_STATUS = "Error while updating processing status to pd_protocol_metadata to DB for ID: {},{}"


# Global DB ORM object
def init_db(app):
    """ Returns db context"""

    # register database instance
    db_context.init_app(app)

    # create schema
    with app.app_context():

        # Create schema if not already created
        db_context.create_all()


# def update_doc_processing_status(id: str, service_name, process_status, qc_status: QcStatus = None):
#     """ Receives id for the document being processed along with percent_complete and present status of document
#         If the document id being processed is present in DB, this function will update the percent_complete and
#         status of document.
#         If document id is not present in the DB, it will return a message saying document id not available"""

#     resource = get_doc_resource_by_id(id)
#     if resource is not None:
#         resource.percentComplete = process_status
#         resource.status = service_name

#         if qc_status is not None:
#             resource.qcStatus = qc_status.value

#         resource.lastUpdated = datetime.utcnow()

#         try:
#             db_context.session.commit()
#             return True
#         except Exception as ex:
#             db_context.session.rollback()
#             exception = ManagementException(
#                 id, ErrorCodes.ERROR_PROCESSING_STATUS)
#             received_documentprocessing_error_event(exception.__dict__)
#             logger.error(ERROR_PROCESSING_STATUS.format(id, ex))

#     return False


def update_doc_resource_by_id(aidoc_id, resource):
    """
    Updates DB resource based on aidoc_id
    """
    resource.lastUpdated = datetime.utcnow()

    try:
        db_context.session.commit()
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(
            aidoc_id, ErrorCodes.ERROR_PROCESSING_STATUS)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error(ERROR_PROCESSING_STATUS.format(aidoc_id, ex))

    return resource


def create_doc_Processing_status(work_flow_id, doc_uid, work_flow_name, doc_file_path, protocol_name):
    session = db_context.session
    status = WorkFlowStatus(
        work_flow_id=work_flow_id, protocol_name=protocol_name, doc_uid=doc_uid, work_flow_name=work_flow_name, documentFilePath=doc_file_path)
    try:
        session.add(status)
        session.commit()
    except Exception as e:
        if not isinstance(e.orig, UniqueViolation):
            raise e
        return False
    return True


def get_work_flow_status_by_id(_id):
    obj = {}
    session = db_context.session
    obj = session.query(WorkFlowStatus).get(_id)
    if obj is not None:
        return schema_to_dict(obj)
    else:
        return None


def get_details_by_elm(table_name, elm_name, elm_val):
    obj = {}
    session = db_context.session
    obj = session.query(table_name).filter(elm_name == elm_val).first()
    return schema_to_dict(obj)


def check_if_document_processed(doc_uid):
    """
    """
    session = db_context.session
    obj_list = session.query(WorkFlowStatus).filter(and_(WorkFlowStatus.doc_uid == doc_uid,
                                                         or_(WorkFlowStatus.work_flow_name == DWorkFLows.FULL_FLOW.value,
                                                             WorkFlowStatus.work_flow_name == DWorkFLows.DIGITIZATION.value),
                                                         WorkFlowStatus.status == WorkFlowState.COMPLETED.value)).all()
    if obj_list:
        return True
    return False

def schema_to_dict(row):
    data = {}
    for column in row.__table__.columns:
        data[column.name] = (getattr(row, column.name))
    return data

# def update_run_id(aidoc_id: str):
#     """
#     Increments runId
#         Input: doc id
#         Ouput: New Run id
#     """
#     resource = get_doc_resource_by_id(aidoc_id)
#     if resource is not None:
#         run_id = resource.runId
#         next_run_id = run_id + 1
#         resource.runId = next_run_id
#
#         resource.lastUpdated = datetime.utcnow()
#
#         try:
#             db_context.session.commit()
#             return next_run_id
#         except Exception as ex:
#             db_context.session.rollback()
#
#             exception = ManagementException(id, ErrorCodes.ERROR_PROCESSING_STATUS)
#             received_documentprocessing_error_event(exception.__dict__)
#             logger.error(ERROR_PROCESSING_STATUS.format(id, ex))


# def received_feedbackcomplete_event(id, feedback_status: FeedbackStatus):
#     resource = get_doc_status_processing_by_id(id, full_mapping=True)
#
#     if resource is not None:
#         resource.feedback = feedback_status.name
#         resource.lastUpdated = datetime.utcnow()
#         # log message for feedback received is updated to DB from users/reviewers
#         logger.info("Feedback received for id is updated to DB: {}".format(id))
#         try:
#             db_context.session.commit()
#             return True
#         except Exception as ex:
#             db_context.session.rollback()
#
#             exception = ManagementException(id, ErrorCodes.ERROR_PROCESSING_STATUS)
#             received_documentprocessing_error_event(exception.__dict__)
#             logger.error(ERROR_PROCESSING_STATUS.format(id, ex))
#
#     return False


def add_compare_event(session, compare_protocol_list, id_):
    try:
        if compare_protocol_list:
            compare_db_data = list()
            for row in compare_protocol_list:
                compare = Documentcompare()
                compare.compareId = row['compare_id']
                compare.id1 = row['id1']
                compare.id2 = row['id2']
                compare.protocolNumber = row['protocolNumber']
                compare.redactProfile = row['redact_profile']
                compare.compareRun = 0
                compare.doc1runId = 0
                compare.doc2runId = 0
                compare.createdDate = datetime.utcnow()
                compare.updatedDate = datetime.utcnow()
                compare_db_data.append(compare)

            session.add_all(compare_db_data)
            session.commit()
            return True
    except Exception as ex:
        logger.error(
            "Error while writing record to PD_document_compare file in DB for ID: {},{}".format(id_, ex))
        session.rollback()
        exception = ManagementException(id_, ErrorCodes.ERROR_PROTOCOL_DATA)
        received_documentprocessing_error_event(exception.__dict__, session)
        return False


def received_comparecomplete_event(session, compare_dict):
    if not compare_dict.get('compare_id',None):
        return
    resource = session.query(Documentcompare).filter(
        Documentcompare.compareId == compare_dict.get('compare_id', '')).first()
    try:
        flow_id = compare_dict['flow_id']
        resource.compareId = compare_dict.get('compare_id', '')
        resource.compareIqvXmlPath = compare_dict.get('IQVXMLPath', '')
        resource.compareCSVPath = compare_dict.get('CSVPath', '')
        resource.compareJSONPath = compare_dict.get('JSONPath', '')
        resource.numChangesTotal = int(compare_dict.get('NumChangesTotal', ''))
        resource.compareCSVPathNormSOA = compare_dict.get('CSVPathNormSOA', '')
        resource.compareJSONPathNormSOA = compare_dict.get(
            'JSONPathNormSOA', '')
        resource.compareExcelPathNormSOA = compare_dict.get(
            'ExcelPathNormSOA', '')
        resource.compareHTMLPathNormSOA = compare_dict.get(
            'HTMLPathNormSOA', '')
        resource.compareJSONPathNormSOA = compare_dict.get(
            'JSONPathNormSOA', '')
        resource.compareExcelPathNormSOA = compare_dict.get(
            'ExcelPathNormSOA', '')
        resource.compareHTMLPathNormSOA = compare_dict.get(
            'HTMLPathNormSOA', '')
        resource.updatedDate = datetime.utcnow()
        session.add(resource)
        session.commit()

        # update compare run no of a document
        update_compare_run(compare_dict['compare_id'], session)
        # update run no of each document in compare process
        update_document_run_no(compare_dict['compare_id'], session)
    except Exception as ex:
        session.rollback()
        exception = ManagementException(
            flow_id, ErrorCodes.ERROR_PROTOCOL_DATA)
        received_documentprocessing_error_event(exception.__dict__, session)
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(
            compare_dict['compare_id'], ex))


def document_compare_all_permutations(session, work_flow_id, flow_name):
    """
    ids_compare_protocol:
    """
    from etmfa.db.feedback_utils import get_latest_file_path
    redact_profile_list = {"profile_0", "profile_1"}
    obj = session.query(WorkFlowStatus).get(work_flow_id)
    protocol_number = obj.protocol_name
    document_path = obj.documentFilePath
    document_path = document_path[:document_path.rfind('\\')]
    if not protocol_number:
        return []
    # consider all workflows in which digitization runs.
    ids_compare_protocol = session.query(WorkFlowStatus.work_flow_id,
                                         WorkFlowStatus.protocol_name,
                                         WorkFlowStatus.documentFilePath
                                         ).filter(and_(WorkFlowStatus.protocol_name == protocol_number,
                                                       WorkFlowStatus.work_flow_id != work_flow_id,
                                                       WorkFlowStatus.work_flow_name == DWorkFLows.FULL_FLOW.value,
                                                       WorkFlowStatus.status == WorkFlowState.COMPLETED.value
                                                       )).all()
    IQVXMLPath1 = get_latest_file_path(
        document_path, prefix="D2_", suffix="*.xml*")
    ids_list = [row['work_flow_id'] for row in ids_compare_protocol]
    ids_compare_protocol_list = list()
    for row in ids_compare_protocol:
        IQVXMLPath2_documentFilePath = row['documentFilePath'][:row.documentFilePath.rfind(
            '\\')]
        IQVXMLPath2 = get_latest_file_path(
            IQVXMLPath2_documentFilePath, prefix='D2_', suffix="*.xml*")
        # if digitization doesnt run for any of flow path will be null
        if IQVXMLPath2:
            for redact_profile in redact_profile_list:
                ids_compare_protocol_list.extend([{'compare_id': str(uuid.uuid4()),
                                                   'id1': work_flow_id,
                                                   'flow_id': work_flow_id,
                                                   'flow_name': flow_name,
                                                   'IQVXMLPath1': IQVXMLPath1,
                                                   'id2': row['work_flow_id'],
                                                   'protocolNumber': protocol_number,
                                                   'IQVXMLPath2': IQVXMLPath2,
                                                   'redact_profile': redact_profile
                                                   },
                                                  {'compare_id': str(uuid.uuid4()),
                                                 'id1': row['work_flow_id'],
                                                   'flow_id':work_flow_id,
                                                   'flow_name':flow_name,
                                                   'IQVXMLPath1': IQVXMLPath2,
                                                   'id2': work_flow_id,
                                                   'protocolNumber': protocol_number,
                                                   'IQVXMLPath2': IQVXMLPath1,
                                                   'redact_profile': redact_profile
                                                   }
                                                  ])
    ret_val = add_compare_event(
        session, ids_compare_protocol_list, work_flow_id)
    return ids_compare_protocol_list if ret_val else []


def document_compare_tuple(session, work_flow_id, flow_name, id1, id2, document_path_1, document_path_2, protocol_number):
    """
    work_flow_id: document compare may run as a part of some workflow
    id1:reference id1
    id2: reference id2
    """
    from etmfa.db.feedback_utils import get_latest_file_path
    redact_profile_list = {"profile_0", "profile_1"}
    document_path_1 = document_path_1[:document_path_1.rfind('\\')]
    IQVXMLPath1 = get_latest_file_path(
        document_path_1, prefix="D2_", suffix="*.xml*")
    ids_compare_protocol_list = []
    document_path_2 = document_path_2[:document_path_2.rfind('\\')]
    IQVXMLPath2 = get_latest_file_path(
        document_path_2, prefix='D2_', suffix="*.xml*")

    for redact_profile in redact_profile_list:
        ids_compare_protocol_list.extend([{'compare_id': str(uuid.uuid4()),
                                           'flow_id': work_flow_id,
                                           'id1': id1,
                                           'flow_name': flow_name,
                                           'IQVXMLPath1': IQVXMLPath1,
                                           'id2': id2,
                                           'protocolNumber': protocol_number,
                                           'IQVXMLPath2': IQVXMLPath2,
                                           'redact_profile': redact_profile
                                           },
                                          {'compare_id': str(uuid.uuid4()),
                                         'id1': id2,
                                           'flow_name': flow_name,
                                           'flow_id': work_flow_id,
                                           'IQVXMLPath1': IQVXMLPath2,
                                           'id2': id1,
                                           'protocolNumber': protocol_number,
                                           'IQVXMLPath2': IQVXMLPath1,
                                           'redact_profile': redact_profile
                                           }
                                          ])
    ret_val = add_compare_event(
        session, ids_compare_protocol_list, work_flow_id)
    return ids_compare_protocol_list if ret_val else []


def insert_into_alert_table(finalattributes):
    doc_status = PDProtocolMetadata.query.filter(
        PDProtocolMetadata.id == finalattributes['AiDocId']).first()
    doc_status_flag = doc_status and doc_status.documentStatus in config.VALID_DOCUMENT_STATUS_FOR_ALERT
    approval_date_flag = finalattributes['approval_date'] != '' and len(
        finalattributes['approval_date']) == 8 and finalattributes['approval_date'].isdigit()
    if doc_status_flag and approval_date_flag and finalattributes['ProtocolNo']:

        # The query below is to check if the approval date for protocol which alert needs to be generated
        # greater than all other approval dates for the protocols.
        resources = db_context.session.query(PDProtocolQCSummaryData,
                                             PDProtocolQCSummaryData.source,
                                             PDProtocolQCSummaryData.approvalDate,
                                             func.rank().over(partition_by=PDProtocolQCSummaryData.aidocId,
                                                              order_by=PDProtocolQCSummaryData.source.desc()).label(
                                                 'rank')).filter(
            and_(PDProtocolQCSummaryData.protocolNumber == finalattributes['ProtocolNo'],
                 PDProtocolQCSummaryData.aidocId != finalattributes['AiDocId'])).all()

        if resources is not None and type(resources) == list and len(resources) > 0:
            resources = [
                resource for resource in resources if resource.rank == 1]
            resources = [
                resource for resource in resources if resource.rank == 1]
            alert_res = all(
                [datetime.strptime(finalattributes['approval_date'], '%Y%m%d').date() > resource.approvalDate for
                 resource in resources])
        else:
            alert_res = True

        if alert_res:
            protocolalert_list = list()
            pd_user_protocol_list = PDUserProtocols.query.filter(
                and_(PDUserProtocols.protocol == finalattributes['ProtocolNo'],
                     PDUserProtocols.follow == True)).all()

            for pd_user_protocol in pd_user_protocol_list:
                protocolalert = Protocolalert()
                protocolalert.aidocId = finalattributes['AiDocId']
                protocolalert.protocol = finalattributes['ProtocolNo']
                protocolalert.protocolTitle = finalattributes['ProtocolTitle']
                protocolalert.id = pd_user_protocol.id
                protocolalert.isActive = True
                protocolalert.emailSentFlag = False
                protocolalert.readFlag = False
                protocolalert.approvalDate = finalattributes['approval_date']
                time_ = datetime.utcnow()
                protocolalert.timeCreated = time_
                protocolalert.timeUpdated = time_
                protocolalert_list.append(protocolalert)

            db_context.session.add_all(protocolalert_list)
            db_context.session.commit()
    else:
        logger.info("Could not insert record to pd_protocol_alert for ID: {}, approval_date:{}, protocol no:{}".format(
            finalattributes['AiDocId'], finalattributes['approval_date'], finalattributes['ProtocolNo']))


# def received_finalizationcomplete_event(id, finalattributes, message_publisher):
#     try:
#         from etmfa.db import table_update_utils
#         FeedbackRunId = finalattributes.get('FeedbackRunId', 0)
#         finalattributes = finalattributes['db_data']

#         resource = get_doc_resource_by_id(id)
#         resource.isProcessing = False
#         resource.isActive = True

#         table_update_utils.update_protocol_metadata(
#             id, FeedbackRunId, finalattributes)
#         protocoldata = table_update_utils.upsert_protocol_data(
#             FeedbackRunId, finalattributes)
#         protocolqcdata = table_update_utils.upsert_protocol_qcdata(
#             FeedbackRunId, finalattributes)
#         protocol_summary_entities = table_update_utils.upsert_summary_entities(
#             FeedbackRunId, finalattributes)
#         table_update_utils.update_protocol_metadata(
#             id, FeedbackRunId, finalattributes)
#         protocoldata = table_update_utils.upsert_protocol_data(
#             FeedbackRunId, finalattributes)
#         protocolqcdata = table_update_utils.upsert_protocol_qcdata(
#             FeedbackRunId, finalattributes)
#         protocol_summary_entities = table_update_utils.upsert_summary_entities(
#             FeedbackRunId, finalattributes)

#         # Entry in summary table
#         summary_json_dict = ast.literal_eval(finalattributes['summary'])
#         summary_dict = {k: v for k, v, _ in summary_json_dict['data']}

#         source = config.SRC_EXTRACT if FeedbackRunId == 0 else config.SRC_FEEDBACK_RUN
#         summary_record = utils.get_updated_qc_summary_record(doc_id=id, source=source, summary_dict=summary_dict,
#                                                              is_active_flg=True, FeedbackRunId=FeedbackRunId)

#         db_context.session.merge(protocoldata)
#         db_context.session.merge(protocolqcdata)
#         db_context.session.merge(summary_record)

#         if finalattributes.get('summary_entities', {}):
#             db_context.session.merge(protocol_summary_entities)

#         db_context.session.commit()

#         # No documents sent for QC by default
#         qc_status = None if FeedbackRunId == 0 else QcStatus.COMPLETED
#         update_doc_processing_status(
#             id=id, process_status=ProcessingStatus.PROCESS_COMPLETED, qc_status=qc_status)
#         update_doc_processing_status(
#             id=id, process_status=ProcessingStatus.PROCESS_COMPLETED, qc_status=qc_status)

#         compare_request_list = document_compare(finalattributes['AiDocId'], finalattributes['ProtocolNo'],
#                                                 finalattributes['documentPath'])

#         if FeedbackRunId == 0:
#             insert_into_alert_table(finalattributes)
#             generate_email.SendEmail.send_status_email(
#                 finalattributes['AiDocId'])
#             generate_email.SendEmail.send_status_email(
#                 finalattributes['AiDocId'])

#         return compare_request_list

#     except Exception as ex:
#         logger.error(
#             f"Exception in received_finalizationcomplete_event() for ID[{id}] : {str(ex)}")
#         logger.error(
#             f"Exception in received_finalizationcomplete_event() for ID[{id}] : {str(ex)}")
#         db_context.session.rollback()
#         exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
#         send_to_error_queue(exception.__dict__, message_publisher)
#         return


def send_to_error_queue(error_dict, message_publisher):
    """
    Sends the error details to error RMQ
    """
    try:
        error_queue_name = EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value
        logger.warning(
            f"Sending error_dict{error_dict} to error queue: {error_queue_name}")
        message_publisher.send_dict(error_dict, error_queue_name)
    except Exception as exc:
        logger.error(
            f"Received exception while sending {error_dict} to error processing queue {error_queue_name}: {str(exc)}")


def received_documentprocessing_error_event(error_dict, session=None):
    doc_id = error_dict.get('id')
    resource = get_work_flow_resource_by_id(doc_id, session)
    session = db_context.session if not session else session
    if resource is not None:
        # Update error status for the document
        resource.errorCode = error_dict.get('error_code', '')
        resource.errorReason = error_dict.get(
            'service_name', '') + error_dict.get('error_message', '')
        resource.status = "ERROR"
        resource.isProcessing = False
        resource.lastUpdated = datetime.utcnow()

        try:
            session.commit()
            logger.warning(
                f"Updated error status to pd_protocol_metadata table. Error details: {error_dict}")
        except Exception as ex:
            session.rollback()
            logger.error(
                f"Error while storing error message to pd_protocol_metadata DB table for ID[{doc_id}]: {str(ex)}")
    else:
        logger.error(NO_RESOURCE_FOUND.format(doc_id))


def pd_fetch_summary_data(aidocid, userid, source=config.SRC_QC):
    try:
        if source == config.SRC_QC:
            resource = Protocolqcdata.query.filter(
                Protocolqcdata.id == aidocid).first()
        else:
            resource = Protocoldata.query.filter(
                Protocoldata.id == aidocid).first()

        if resource:
            summary = ast.literal_eval(json.loads(resource.iqvdataSummary))
            summary_dict = {k: v for k, v, _ in summary['data']}
        else:
            return None

        summary_record = utils.get_updated_qc_summary_record(doc_id=aidocid, source=source, summary_dict=summary_dict,
                                                             is_active_flg=True, qc_approved_by=userid)
        db_context.session.merge(summary_record)
        db_context.session.commit()
        return aidocid
    except Exception as ex:
        logger.error(ERROR_PROCESSING_STATUS.format(aidocid, str(ex)))
        db_context.session.rollback()
        exception = ManagementException(
            aidocid, ErrorCodes.ERROR_QC_SUMMARY_DATA)
        received_documentprocessing_error_event(exception.__dict__)


def save_doc_processing(request, _id, doc_path):
    resource = PDProtocolMetadata.from_post_request(request, _id)
    resource.documentFilePath = doc_path
    resource.userId = request['userId']
    resource.fileName = request['sourceFileName']
    resource.versionNumber = request['versionNumber']
    resource.protocol = request['protocolNumber']
    resource.sponsor = request['sponsor']
    resource.sourceSystem = request['sourceSystem']
    resource.documentStatus = request['documentStatus']
    resource.studyStatus = request['studyStatus']
    resource.amendment = request['amendmentNumber']
    resource.projectId = request['projectID']
    resource.environment = request['environment']
    resource.indication = request['indication']
    resource.moleculeDevice = request['moleculeDevice']
    resource.percentComplete = ProcessingStatus.PROCESS_STARTED.value
    resource.status = 'TRIAGE_STARTED' #hardcoded for compatiblity will be rmeoved w.r.t workflows
    resource.qcStatus = QcStatus.NOT_STARTED.value
    resource.runId = 0

    try:
        db_context.session.add(resource)
        db_context.session.commit()
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_SAVING)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error(ERROR_PROCESSING_STATUS.format(_id, ex))


# def get_doc_processing_by_id(id, full_mapping=False):
#     resource_dict = get_doc_resource_by_id(id)
#     return resource_dict


# def get_doc_processed_by_id(id, full_mapping=True):
#     resource_dict = get_doc_attributes_by_id(id)

#     return resource_dict


# def get_doc_proc_metrics_by_id(id, full_mapping=True):
#     resource_dict = get_doc_metrics_by_id(id)

#     return resource_dict


def get_file_contents_by_id(protocol_number: str, aidoc_id: str, protocol_number_verified: bool = False) -> str:
    """
    Extracts file toc json by aidoc_id

    If protocol_number and aidoc_id are already verified, then extract contents directly from data.
        If not verified by joining with metadata table before extracting contents
    """
    cleaned_inputs = utils.clean_inputs(
        protocol_number=protocol_number, aidoc_id=aidoc_id)
    protocol_number = cleaned_inputs.get('protocol_number', '')
    aidoc_id = cleaned_inputs.get('aidoc_id', '')

    try:

        resource = db_context.session.query(Protocoldata.id, Protocoldata.iqvdataToc
                                            ).join(PDProtocolMetadata, and_(PDProtocolMetadata.id == Protocoldata.id,
                                                                            PDProtocolMetadata.protocol == protocol_number,
                                                                            PDProtocolMetadata.qcStatus == 'QC_COMPLETED',
                                                                            Protocoldata.id == aidoc_id)
                                                   ).first()
        if resource:
            result = resource[1]
        else:
            result = None
    except Exception as e:
        logger.error(NO_RESOURCE_FOUND.format(aidoc_id))
        result = None
    return result


# def get_compare_documents(base_doc_id, compare_doc_id):
#     basedocid = base_doc_id
#     comparedocid = compare_doc_id
#     resource_IQVdata = None
#     resource = Documentcompare.query.filter(Documentcompare.id1 == basedocid, Documentcompare.id2 == comparedocid).first()
#     flag_order=1
#     if resource is None:
#         resource = Documentcompare.query.filter(Documentcompare.id1 == comparedocid,
#                                                 Documentcompare.id2 == basedocid).first()
#         flag_order=-1
#
#     else:
#         None
#     # to check none
#     if resource is not None:
#         resource_IQVdata = resource.iqvdata
#     else:
#         logger.error(NO_COMPARE_RESOURCE_FOUND.format(basedocid, comparedocid))
#
#     return resource_IQVdata


# def get_doc_metrics_by_id(id):
#     g.aidocid = id
#     resource = Metric.query.filter(Metric.id.like(str(id))).first()
#
#     if resource is None:
#         logger.error(NO_RESOURCE_FOUND.format(id))
#
#     return resource


def get_doc_status_processing_by_id(id, full_mapping=True, session=None):
    resource_dict = get_doc_resource_by_id(id, session)

    return resource_dict


# def get_compare_resource_by_compare_id(comparevalues):
#     compareid = comparevalues['COMPARE_ID']
#     resource = Documentcompare.query.filter(Documentcompare.compareId == compareid).first()
#
#     if resource is None:
#         logger.error(NO_RESOURCE_FOUND.format(compareid))
#     return resource


def get_doc_resource_by_id(_id, session=None):
    """
    session: None if function used in flask context
    """
    if not session:
        g.aidocid = _id
    # resource = PDProtocolMetadata.query.filter(PDProtocolMetadata.id.like(str(id))).first()
    session = session if session else db_context.session
    resource = session.query(PDProtocolMetadata).filter(
        PDProtocolMetadata.id == _id).first()
    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(_id))

    return resource


def get_work_flow_resource_by_id(_id, session=None):
    """
    session: None if function used in flask context
    """
    if not session:
        g.aidocid = _id
    # resource = PDProtocolMetadata.query.filter(PDProtocolMetadata.id.like(str(id))).first()
    session = session if session else db_context.session
    resource = session.query(WorkFlowStatus).get(_id)
    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(_id))

    return resource

# def get_user_protocol_by_id(id):
#     g.aidocid = id
#     resource = PDUserProtocols.query.filter(PDUserProtocols.id.like(str(id))).first()
#
#     if resource is None:
#         logger.error(NO_RESOURCE_FOUND.format(id))
#
#     return resource


# def upsert_attributevalue(doc_processing_id, namekey, value):
#     g.aidocid = id
#     doc_processing_resource = get_doc_attributes_by_id(doc_processing_id)
#
#     if doc_processing_resource is None:
#         logger.error(NO_RESOURCE_FOUND.format(id))
#     else:
#         try:
#             setattr(doc_processing_resource, namekey, value)
#             db_context.session.commit()
#         except Exception as ex:
#             db_context.session.rollback()
#             exception = ManagementException(id, ErrorCodes.ERROR_UPDATING_ATTRIBUTES)
#             received_documentprocessing_error_event(exception.__dict__)
#             logger.error("Error while updating attribute to PD_protocol_data to DB for ID: {},{}".format(
#                 doc_processing_id, ex))


# def get_attribute_dict(doc_processing_id):
#     doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
#
#     if doc_processing_resource is None:
#         logger.error(NO_RESOURCE_FOUND.format(id))
#
#     return doc_processing_resource


def safe_unicode(obj, *args):
    """ return the unicode representation of obj """
    try:
        return str(obj, *args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return str(ascii_text)


def get_latest_record(sponsor, protocol_number, version_number):
    """ to get the latest record based on sponsor, protocol_number, version_number"""
    resource = PDProtocolMetadata.query.filter(PDProtocolMetadata.sponsor == sponsor,
                                               PDProtocolMetadata.protocol == protocol_number,
                                               PDProtocolMetadata.versionNumber == version_number).order_by(
        PDProtocolMetadata.timeCreated.desc()).first()

    return resource


# def set_draft_version(document_status, sponsor, protocol, version_number):
#     # to set draft version for documents
#     if not version_number:
#         version_number = '-0.01'
#
#     if document_status == 'draft':
#         resource = get_latest_record(sponsor, protocol, version_number)
#
#         if resource is None:
#             draftVersion = float(version_number) + 0.01
#         else:
#             if resource.documentStatus == 'draft':
#                 old_draftVersion = resource.draftVersion
#                 draftVersion = float(old_draftVersion) + 0.01
#             else:
#                 draftVersion = float(version_number) + 0.01
#     else:
#         draftVersion = None
#     return draftVersion


def get_latest_protocol(protocol_number, version_number="", approval_date="", aidoc_id="", document_status="",
                        qc_status="", is_top_1_only=True):
    """
    Get top-1 or all the protocol based on input arguments
    """
    resource = None

    # Get dynamic conditions
    all_filter, order_condition = utils.get_filter_conditions(protocol_number, version_number, approval_date, aidoc_id,
                                                              document_status)
    try:
        if is_top_1_only:
            resource = db_context.session.query(PDProtocolMetadata, PDProtocolMetadata.draftVersion,
                                                PDProtocolMetadata.amendment, PDProtocolMetadata.uploadDate,
                                                PDProtocolMetadata.documentFilePath, PDProtocolMetadata.id,
                                                PDProtocolMetadata.projectId, PDProtocolMetadata.documentStatus,
                                                PDProtocolMetadata.protocol, PDProtocolMetadata.indication,
                                                PDProtocolMetadata.shortTitle
                                                ).filter(text(all_filter)
                                                                ).order_by(text(order_condition)).first()
        else:
            resource = db_context.session.query(PDProtocolMetadata, PDProtocolMetadata.draftVersion,
                                                PDProtocolMetadata.amendment, PDProtocolMetadata.uploadDate,
                                                PDProtocolMetadata.documentFilePath, PDProtocolMetadata.projectId,
                                                PDProtocolMetadata.documentStatus, PDProtocolMetadata.protocol,
                                                PDProtocolMetadata.source, PDProtocolMetadata.indication,
                                                PDProtocolMetadata.id, PDProtocolMetadata.shortTitle,
                                                func.rank().over(partition_by=PDProtocolMetadata.id,
                                                                 order_by=PDProtocolMetadata.source.desc()).label(
                                                    'rank')
                                                ).filter(text(all_filter)
                                                                ).order_by(text(order_condition)).all()
            resource = utils.filter_qc_status(
                resources=resource, qc_status=qc_status)
    except Exception as e:
        logger.error(
            f"No document resource was found in DB [Protocol: {protocol_number}; Version: {version_number}; approval_date: {approval_date}; \
            doc_id: {aidoc_id}; document_status: {document_status}; qc_status: {qc_status}]")
        logger.error(f"Exception message:\n{e}")

    return resource


def get_record_by_userid_protocol(user_id, protocol_number):
    """
    get record from user_protocol table on userid and protocol fields
    """
    resource = PDUserProtocols.query.filter(PDUserProtocols.userId == user_id).filter(
        PDUserProtocols.protocol == protocol_number).all()

    return resource


def get_record_by_userid_projectid(user_id, project_id):
    """
    get record from user_protocol table on userid and projectid fields
    """
    resource = PDUserProtocols.query.filter(PDUserProtocols.userId == user_id,
                                            PDUserProtocols.projectId == project_id).all()

    return resource


def update_user_protocols(user_id, project_id, protocol_number):
    userprotocols = PDUserProtocols()

    if protocol_number:
        records = get_record_by_userid_protocol(user_id, protocol_number)

    if not protocol_number and project_id is not None:
        records = get_record_by_userid_projectid(user_id, project_id)

    if not records:
        userprotocols.isActive = True
        userprotocols.follow = True
        userprotocols.userId = user_id
        userprotocols.projectId = project_id
        userprotocols.protocol = protocol_number
        userprotocols.userRole = config.UPLOADED_USERROLE
        userprotocols.redactProfile = config.USERROLE_REDACTPROFILE_MAP.get(
            config.UPLOADED_USERROLE)
        try:
            db_context.session.add(userprotocols)
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            logger.error("Error while writing record to PD_user_protocol file in DB for user id: {},{}".format(user_id, ex))
    else:
        for record in records:
            record.isActive = True
            record.follow = True
            record.userRole = config.UPLOADED_USERROLE
            record.redactProfile = config.USERROLE_REDACTPROFILE_MAP.get(
                config.UPLOADED_USERROLE)
            record.lastUpdated = datetime.utcnow()
            try:
                db_context.session.merge(record)
                db_context.session.commit()
            except Exception as ex:
                db_context.session.rollback()
                logger.error("Error while updating record to PD_user_protocol file in DB for user id: {},{}".format(user_id, ex))

def get_attr_soa_details(protocol_number, aidoc_id) -> dict:
    """
    Get protocol attributes and Normalized SOA
    """
    norm_soa = []
    visitrecord_mapper = None
    resource_dict = dict()
    norm_dict = dict()
    footnotes = ["footnote_0", "footnote_1", "footnote_2", "footnote_3", "footnote_4",
                 "footnote_5", "footnote_6", "footnote_7", "footnote_8", "footnote_9"]
    try:
        active_protocol = PDProtocolMetadata.query.filter(
            and_(PDProtocolMetadata.id == aidoc_id, PDProtocolMetadata.protocol == protocol_number,
                 PDProtocolMetadata.isActive == True)).first()
        if active_protocol is None:
            return resource_dict

    except Exception as e:
        logger.error(
            f"No active document found in DB [Protocol: {protocol_number}; aidoc_id: {aidoc_id}]")
        logger.error(f"Exception message:\n{e}")
    
    try:
        session = db_context.session()

        helper_obj = MetaDataTableHelper()  
        protocol_attributes_str = helper_obj.get_data(aidoc_id)

        visitrecord_mapper = session.query(IqvassessmentvisitrecordDbMapper).filter(
            IqvassessmentvisitrecordDbMapper.doc_id == aidoc_id).all()   
        
        if visitrecord_mapper is not None:
            for record in visitrecord_mapper:
                resource_dict = {key: value for key,
                                 value in record.__dict__.items()}
                resource_dict.pop("_sa_instance_state")
                footnote_list = []
                for note in footnotes:
                    if note in resource_dict:
                        if len(resource_dict.get(note)) != 0:
                            footnote_list.append(resource_dict.get(note))
                        resource_dict.pop(note)
                    continue

                resource_dict.update({"footnotes": footnote_list})
                norm_soa.append(resource_dict)
            norm_soa_str = json.loads(json.dumps(norm_soa))
        
        norm_dict = {
            'id': aidoc_id, 'protocolAttributes': protocol_attributes_str, 'normalizedSOA': norm_soa_str}
    except Exception as exc:
        logger.exception(
            f"Exception received while formatting the data [Protocol: {protocol_number}; aidoc_id: {aidoc_id}]. Exception: {str(exc)}")

    return norm_dict

def get_attr_soa_compare(protocol_number, aidoc_id, compare_doc_id) -> dict:
    """
    Get Normalized SOA Difference
    """
    redact_profile = config.USERROLE_REDACTPROFILE_MAP.get('primary')
    resource = None
    resource_dict = dict()
    norm_soa_diff = ""

    try:
        resource = Documentcompare.query.filter(
            and_(Documentcompare.id1 == aidoc_id, Documentcompare.protocolNumber == protocol_number,
                 Documentcompare.id2 == compare_doc_id,
                 Documentcompare.redactProfile == redact_profile)).all()
        if not resource:
            return resource_dict

        compare_record = max(resource, key=lambda record: record.compareRun)
        JSONPathNormSOA = Path(compare_record.compareJSONPathNormSOA)
        if JSONPathNormSOA:
            with open(JSONPathNormSOA, 'rb') as file_obj:
                norm_soa_diff = json.load(file_obj)
                file_obj.close()
        else:
            return abort(NO_RESOURCE_FOUND.format(protocol_number, aidoc_id, compare_doc_id))

        resource_dict = {'normalizedSOADifference': norm_soa_diff}
    except Exception as exc:
        logger.exception(
            f"Exception received while formatting the data [Protocol: {protocol_number}; aidoc_id: {aidoc_id}; compare_id: {compare_doc_id}]. Exception: {str(exc)}")

    return resource_dict


def update_compare_run(compare_id, session):
    """
        update the compareRun i.e, how many times compare process runs for particular combination.
    """
    try:
        resource = session.query(Documentcompare).filter(
            Documentcompare.compareId == compare_id).first()
        document_compare_list = session.query(Documentcompare).filter(and_(Documentcompare.id1 == resource.id1,
                                                                           Documentcompare.id2 == resource.id2,
                                                                           Documentcompare.redactProfile == resource.redactProfile)).all()
        if len(document_compare_list) == 1:
            compare_run_count = 0
        else:
            compare_record = max(document_compare_list,
                                 key=lambda record: record.compareRun)
            compare_run_count = compare_record.compareRun
            compare_run_count += 1
        resource.compareRun = compare_run_count
        session.add(resource)
        session.commit()
    except Exception as exc:
        logger.exception(
            f"No Document found for [aidoc_id: {resource.id1}; compare_base_id: {resource.id2}; redact_profile: {resource.redactProfile}]. Exception: {str(exc)}")


def update_document_run_no(compare_id, session):
    """
        update the document run no of id1 and id2 for which comparison occurred.
    """
    try:
        resource = session.query(Documentcompare).filter(
            Documentcompare.compareId == compare_id).first()
        metadata_resource = get_doc_resource_by_id(resource.id1, session)
        doc1_run_no = metadata_resource.runId
        resource.doc1runId = doc1_run_no

        metadata_resource = get_doc_resource_by_id(resource.id2, session)
        doc2_run_no = metadata_resource.runId
        resource.doc2runId = doc2_run_no

        session.add(resource)
        session.commit()
    except Exception as exc:
        logger.exception(
            f"No Document found for [compare_id: {compare_id}].Exception: {str(exc)}")


# added for pd 2.0
def get_normalized_soa_details(protocol_number, aidoc_id) -> dict:
    """
    Get protocol Normalized SOA
    """
    visitrecord_mapper = None
    resource_dict = dict()
    norm_dict = dict()
    norm_soa_str= dict()
    
    footnotes = ["footnote_0", "footnote_1", "footnote_2", "footnote_3", "footnote_4",
                 "footnote_5", "footnote_6", "footnote_7", "footnote_8", "footnote_9"]
    norm_soa = []
    try:
        session = db_context.session()

        visitrecord_mapper = session.query(IqvassessmentvisitrecordDbMapper).filter(
            IqvassessmentvisitrecordDbMapper.doc_id == aidoc_id).all()

        if visitrecord_mapper is not None:
            for record in visitrecord_mapper:
                resource_dict = {key: value for key,
                                 value in record.__dict__.items()}
                resource_dict.pop("_sa_instance_state")
                footnote_list = []

                for note in footnotes:
                    if note in resource_dict:
                        if len(resource_dict.get(note)) != 0:
                            footnote_list.append(resource_dict.get(note))
                        resource_dict.pop(note)
                    continue

                resource_dict.update({"footnotes": footnote_list})
                norm_soa.append(resource_dict)
                norm_soa_str = json.loads(json.dumps(norm_soa))

            norm_dict = {'id': aidoc_id, 'normalizedSOA': norm_soa_str}

    except Exception as exc:
        logger.exception(
            f"Exception received while formatting the data [Protocol: {protocol_number}; aidoc_id: {aidoc_id}]. Exception: {str(exc)}")

    return norm_dict



def get_metadata_summary(op, aidocId, fieldName=None) -> dict:
    """
    Get metadata summary fields 
    """
    response_dict = {}
    try:
        helper_obj = MetaDataTableHelper()
        if op == 'metadata':
            metadata = helper_obj.get_data(aidocId, fieldName)
        elif op == 'metaparam':
            metadata = helper_obj.getMetaParam(aidocId)
        else:
            raise Exception("invalid op value.")
        
        response_dict_str = json.loads(json.dumps(metadata, default=str))
        response_dict["data"] = response_dict_str
        
    except Exception as exc:
        logger.exception(
            f"Exception received while formatting the data [aidoc_id: {aidocId}]. Exception: {str(exc)}")
    return response_dict


def add_metadata_summary(op, **data):
    """
    Add metadata summary fields 
    """
    metadata_response = {}
    try:
        helper_obj = MetaDataTableHelper()
        if op == 'addField':
            metadata_response = helper_obj.add_field(data.get("id"), data.get("fieldName"))
        elif op == 'addAttributes':
            metadata_response = helper_obj.add_field_data(data.get("id"), data.get("fieldName"), data.get("attributes"))
        else:
            raise Exception("invalid op value.")
    except Exception as exc:
        logger.exception(
            f"Exception received while formatting the data [op: {op}]. Exception: {str(exc)}")
    return metadata_response


def update_metadata_summary(field_name, **data):
    """
    Update metadata summary fields 
    """
    metadata_response = {}
    try:
        helper_obj = MetaDataTableHelper()   
        if field_name:     
            metadata_response = helper_obj.add_update_attribute(data.get("id"), data.get("fieldName"), data.get("attributes"))  
        else:
            metadata_response = helper_obj.update_primary_attributes(data.get("id"), data.get("attributes"))  
            
    except Exception as exc:
        logger.exception(
            f"Exception received while formatting the data [id: {id}]. Exception: {str(exc)}")
    return metadata_response


def delete_metadata_summary(op, **data):
    """
    Delete metadata summary fields 
    """
    metadata_response = {}
    try:
        helper_obj = MetaDataTableHelper()
        if op == 'deleteAttribute':
            metadata_response = helper_obj.delete_attribute(data.get("id"), data.get("fieldName"), data.get("attributes"))
        elif op == 'deleteField':
             metadata_response = helper_obj.delete_field(data.get("id"), data.get("fieldName"))
        else:
            raise Exception("unknown operation received.")
    except Exception as exc:
        logger.exception(
            f"Exception received while formatting the data [id: {id}]. Exception: {str(exc)}")
    return metadata_response



def get_protocols_by_date_time_range(version_date="", approval_date="", start_date="", end_date="",
                                     document_status="", upload_date="", qc_status=""):
    """
    Get top-1 or all the protocol based on input arguments
    """
    resource = None

    # #Get dynamic conditions
    all_filter = utils.all_filters(
        version_date, approval_date, start_date, end_date, document_status, upload_date, qc_status)

    try:
        if qc_status is not '':
            resource = db_context.session.query( PDProtocolMetadata,
                                                PDProtocolMetadata.draftVersion, PDProtocolMetadata.id,
                                                PDProtocolMetadata.protocol, PDProtocolMetadata.documentFilePath,
                                                PDProtocolMetadata.projectId, PDProtocolMetadata.uploadDate,
                                                PDProtocolMetadata.sponsor, PDProtocolMetadata.protocolTitle,
                                                PDProtocolMetadata.versionNumber, PDProtocolMetadata.documentStatus,
                                                PDProtocolMetadata.protocol, PDProtocolMetadata.amendment,
                                                PDProtocolMetadata.qcStatus, PDProtocolMetadata.indication,
                                                PDProtocolMetadata.approvalDate, PDProtocolMetadata.source,
                                                PDProtocolMetadata.amendment,
                                                PDProtocolMetadata.shortTitle,
                                                PDProtocolMetadata.versionDate,
                                                PDProtocolMetadata.amendmentNumber
                                                ).filter(text(all_filter)).all()
        else:
            resource = db_context.session.query(PDProtocolMetadata,PDProtocolMetadata.id,
                                                PDProtocolMetadata.draftVersion,
                                                PDProtocolMetadata.protocol, PDProtocolMetadata.documentFilePath,
                                                PDProtocolMetadata.projectId, PDProtocolMetadata.uploadDate,
                                                PDProtocolMetadata.sponsor, PDProtocolMetadata.protocolTitle,
                                                PDProtocolMetadata.versionNumber, PDProtocolMetadata.documentStatus,
                                                PDProtocolMetadata.protocol, PDProtocolMetadata.amendment,
                                                PDProtocolMetadata.qcStatus, PDProtocolMetadata.indication,
                                                PDProtocolMetadata.approvalDate, PDProtocolMetadata.source,
                                                PDProtocolMetadata.amendment,
                                                PDProtocolMetadata.shortTitle,
                                                PDProtocolMetadata.versionDate,
                                                PDProtocolMetadata.amendmentNumber
                                                ).filter(text(all_filter)).all()

        resource = utils.filter_qc_status(
            resources=resource, qc_status=qc_status)
    except Exception as e:
        logger.error(f"Exception message:\n{e}")

    return resource
