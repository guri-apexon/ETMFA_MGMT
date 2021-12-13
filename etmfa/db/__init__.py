import ast
import datetime
import logging
import os
import json
import uuid

from datetime import datetime

from etmfa.db.db import db_context
from etmfa.db import utils, generate_email, config
from etmfa.consts import Consts as consts
from etmfa.db.models.documentcompare import Documentcompare
from etmfa.db.models.pd_protocol_data import Protocoldata
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.db.models.pd_protocol_qc_summary_data import PDProtocolQCSummaryData
from etmfa.db.models.pd_protocol_qcdata import Protocolqcdata
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.db.models.pd_protocol_summary_entities import ProtocolSummaryEntities
from etmfa.error import ErrorCodes, ManagementException
from etmfa.messaging.models.processing_status import (FeedbackStatus,
                                                      ProcessingStatus, QcStatus)
from pathlib import Path
from flask import g, abort
from sqlalchemy import and_, func
from sqlalchemy.sql import text
from etmfa.messaging.models.queue_names import EtmfaQueues

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


def update_doc_processing_status(id: str, process_status: ProcessingStatus, qc_status: QcStatus = None):
    """ Receives id for the document being processed along with percent_complete and present status of document
        If the document id being processed is present in DB, this function will update the percent_complete and
        status of document.
        If document id is not present in the DB, it will return a message saying document id not available"""

    resource = get_doc_resource_by_id(id)
    if resource is not None:
        resource.percentComplete = process_status.value
        resource.status = process_status.name

        if qc_status is not None:
            resource.qcStatus = qc_status.value

        resource.lastUpdated = datetime.utcnow()

        try:
            db_context.session.commit()
            return True
        except Exception as ex:
            db_context.session.rollback()

            exception = ManagementException(id, ErrorCodes.ERROR_PROCESSING_STATUS)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error(ERROR_PROCESSING_STATUS.format(id, ex))

    return False


def update_doc_resource_by_id(aidoc_id, resource):
    """
    Updates DB resource based on aidoc_id
    """
    resource.lastUpdated = datetime.utcnow()

    try:
        db_context.session.commit()
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(aidoc_id, ErrorCodes.ERROR_PROCESSING_STATUS)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error(ERROR_PROCESSING_STATUS.format(aidoc_id, ex))

    return resource


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


def add_compare_event(compare_protocol_list, id_):
    try:
        if compare_protocol_list:
            compare_db_data = list()
            for row in compare_protocol_list:
                compare = Documentcompare()
                compare.compareId = row['compareId']
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

            db_context.session.add_all(compare_db_data)
            db_context.session.commit()
            return True
    except Exception as ex:
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(id_, ex))
        db_context.session.rollback()
        exception = ManagementException(id_, ErrorCodes.ERROR_PROTOCOL_DATA)
        received_documentprocessing_error_event(exception.__dict__)
        return False


def received_comparecomplete_event(compare_dict, message_publisher):
    resource = Documentcompare.query.filter(Documentcompare.compareId == compare_dict.get('compare_id', '')).first()
    try:
        resource.compareId = compare_dict.get('compare_id', '')
        resource.compareIqvXmlPath = compare_dict.get('IQVXMLPath', '')
        resource.compareCSVPath = compare_dict.get('CSVPath', '')
        resource.compareJSONPath = compare_dict.get('JSONPath', '')
        resource.numChangesTotal = int(compare_dict.get('NumChangesTotal', '')) if compare_dict.get('NumChangesTotal',
                                                                                                    '').isdigit() else 0
        resource.compareCSVPathNormSOA = compare_dict.get('CSVPathNormSOA', '')
        resource.compareJSONPathNormSOA = compare_dict.get('JSONPathNormSOA', '')
        resource.compareExcelPathNormSOA = compare_dict.get('ExcelPathNormSOA', '')
        resource.compareHTMLPathNormSOA = compare_dict.get('HTMLPathNormSOA', '')
        resource.updatedDate = datetime.utcnow()
        db_context.session.add(resource)
        db_context.session.commit()

        # update compare run no of a document
        update_compare_run(compare_id=compare_dict.get('compare_id', ''))
        # update run no of each document in compare process
        update_document_run_no(compare_id=compare_dict.get('compare_id', ''))
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(compare_dict.get('compare_id', ''), ErrorCodes.ERROR_PROTOCOL_DATA)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(
            compare_dict['compare_id'], ex))


def document_compare(aidocid, protocol_number, document_path):
    from etmfa.db.feedback_utils import get_latest_file_path
    redact_profile_list = {"profile_0", "profile_1"}
    if protocol_number:
        ids_compare_protocol = db_context.session.query(PDProtocolMetadata.id,
                                                        PDProtocolMetadata.protocol,
                                                        PDProtocolMetadata.documentFilePath
                                                        ).filter(and_(PDProtocolMetadata.protocol == protocol_number,
                                                                      PDProtocolMetadata.id != aidocid,
                                                                      PDProtocolMetadata.status == 'PROCESS_COMPLETED'
                                                                      )).all()

        IQVXMLPath1 = get_latest_file_path(document_path, prefix="FIN_", suffix="*.xml*")

        if IQVXMLPath1:
            ids_compare_protocol_1 = list()
            for row in ids_compare_protocol:
                IQVXMLPath2_documentFilePath = row.documentFilePath[:row.documentFilePath.rfind('\\')]
                IQVXMLPath2 = get_latest_file_path(IQVXMLPath2_documentFilePath, prefix='FIN_', suffix="*.xml*")
                if IQVXMLPath2:
                    for redact_profile in redact_profile_list:
                        ids_compare_protocol_1.extend([{'compareId': str(uuid.uuid4()),
                                                        'id1': aidocid,
                                                        'IQVXMLPath1': IQVXMLPath1,
                                                        'id2': row.id,
                                                        'protocolNumber': protocol_number,
                                                        'IQVXMLPath2': IQVXMLPath2,
                                                        'redact_profile': redact_profile
                                                        },
                                                       {'compareId': str(uuid.uuid4()),
                                                        'id1': row.id,
                                                        'IQVXMLPath1': IQVXMLPath2,
                                                        'id2': aidocid,
                                                        'protocolNumber': protocol_number,
                                                        'IQVXMLPath2': IQVXMLPath1,
                                                        'redact_profile': redact_profile
                                                        }
                                                       ])
            ids_compare_protocol = ids_compare_protocol_1
            ret_val = add_compare_event(ids_compare_protocol, aidocid)
            if ret_val:
                return ids_compare_protocol


def insert_into_alert_table(finalattributes):
    doc_status = PDProtocolMetadata.query.filter(PDProtocolMetadata.id == finalattributes['AiDocId']).first()
    doc_status_flag = doc_status and doc_status.documentStatus in config.VALID_DOCUMENT_STATUS_FOR_ALERT
    approval_date_flag = finalattributes['approval_date'] != '' and len(finalattributes['approval_date']) == 8 and \
                         finalattributes['approval_date'].isdigit()
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
            resources = [resource for resource in resources if resource.rank == 1]
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


def received_finalizationcomplete_event(id, finalattributes, message_publisher):
    try:
        from etmfa.db import table_update_utils
        FeedbackRunId = finalattributes.get('FeedbackRunId', 0)
        finalattributes = finalattributes['db_data']

        resource = get_doc_resource_by_id(id)
        resource.isProcessing = False
        resource.isActive = True

        table_update_utils.update_protocol_metadata(id, FeedbackRunId, finalattributes)
        protocoldata = table_update_utils.upsert_protocol_data(FeedbackRunId, finalattributes)
        protocolqcdata = table_update_utils.upsert_protocol_qcdata(FeedbackRunId, finalattributes)
        protocol_summary_entities = table_update_utils.upsert_summary_entities(FeedbackRunId, finalattributes)

        # Entry in summary table
        summary_json_dict = ast.literal_eval(finalattributes['summary'])
        summary_dict = {k: v for k, v, _ in summary_json_dict['data']}

        source = config.SRC_EXTRACT if FeedbackRunId == 0 else config.SRC_FEEDBACK_RUN
        summary_record = utils.get_updated_qc_summary_record(doc_id=id, source=source, summary_dict=summary_dict,
                                                             is_active_flg=True, FeedbackRunId=FeedbackRunId)

        db_context.session.merge(protocoldata)
        db_context.session.merge(protocolqcdata)
        db_context.session.merge(summary_record)

        if finalattributes.get('summary_entities', {}):
            db_context.session.merge(protocol_summary_entities)

        db_context.session.commit()

        # No documents sent for QC by default
        qc_status = None if FeedbackRunId == 0 else QcStatus.COMPLETED
        update_doc_processing_status(id=id, process_status=ProcessingStatus.PROCESS_COMPLETED, qc_status=qc_status)

        compare_request_list = document_compare(finalattributes['AiDocId'], finalattributes['ProtocolNo'],
                                                finalattributes['documentPath'])

        if FeedbackRunId == 0:
            insert_into_alert_table(finalattributes)
            generate_email.SendEmail.send_status_email(finalattributes['AiDocId'])

        return compare_request_list

    except Exception as ex:
        logger.error(f"Exception in received_finalizationcomplete_event() for ID[{id}] : {str(ex)}")
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
        send_to_error_queue(exception.__dict__, message_publisher)
        return


def send_to_error_queue(error_dict, message_publisher):
    """
    Sends the error details to error RMQ
    """
    try:
        error_queue_name = EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value
        logger.warning(f"Sending error_dict{error_dict} to error queue: {error_queue_name}")
        message_publisher.send_dict(error_dict, error_queue_name)
    except Exception as exc:
        logger.error(
            f"Received exception while sending {error_dict} to error processing queue {error_queue_name}: {str(exc)}")


def received_documentprocessing_error_event(error_dict):
    doc_id = error_dict.get('id')
    resource = get_doc_resource_by_id(doc_id)
    if resource is not None:
        # Update error status for the document
        resource.errorCode = error_dict.get('error_code', '')
        resource.errorReason = error_dict.get('service_name', '') + error_dict.get('error_message', '')
        resource.status = "ERROR"

        resource.isProcessing = False
        resource.lastUpdated = datetime.utcnow()

        try:
            db_context.session.commit()
            logger.warning(
                f"Updated error status to pd_protocol_metadata table. Error details: {error_dict}")
        except Exception as ex:
            db_context.session.rollback()
            logger.error(
                f"Error while storing error message to pd_protocol_metadata DB table for ID[{doc_id}]: {str(ex)}")
    else:
        logger.error(NO_RESOURCE_FOUND.format(doc_id))


def pd_fetch_summary_data(aidocid, userid, source=config.SRC_QC):
    try:
        if source == config.SRC_QC:
            resource = Protocolqcdata.query.filter(Protocolqcdata.id == aidocid).first()
        else:
            resource = Protocoldata.query.filter(Protocoldata.id == aidocid).first()

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
        exception = ManagementException(aidocid, ErrorCodes.ERROR_QC_SUMMARY_DATA)
        received_documentprocessing_error_event(exception.__dict__)


def save_doc_processing(request, _id, doc_path):
    resource = PDProtocolMetadata.from_post_request(request, _id, doc_path)

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
    resource.percentComplete = ProcessingStatus.TRIAGE_STARTED.value
    resource.status = ProcessingStatus.TRIAGE_STARTED.name
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


def get_doc_processing_by_id(id, full_mapping=False):
    resource_dict = get_doc_resource_by_id(id).as_dict()

    return resource_dict


# def get_doc_processed_by_id(id, full_mapping=True):
#     resource_dict = get_doc_attributes_by_id(id)
#
#     return resource_dict


# def get_doc_proc_metrics_by_id(id, full_mapping=True):
#     resource_dict = get_doc_metrics_by_id(id)
#
#     return resource_dict


def get_file_contents_by_id(protocol_number: str, aidoc_id: str, protocol_number_verified: bool = False) -> str:
    """
    Extracts file toc json by aidoc_id

    If protocol_number and aidoc_id are already verified, then extract contents directly from data.
        If not verified by joining with metadata table before extracting contents
    """
    cleaned_inputs = utils.clean_inputs(protocol_number=protocol_number, aidoc_id=aidoc_id)
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


def get_doc_status_processing_by_id(id, full_mapping=True):
    resource_dict = get_doc_resource_by_id(id)

    return resource_dict


# def get_compare_resource_by_compare_id(comparevalues):
#     compareid = comparevalues['COMPARE_ID']
#     resource = Documentcompare.query.filter(Documentcompare.compareId == compareid).first()
#
#     if resource is None:
#         logger.error(NO_RESOURCE_FOUND.format(compareid))
#     return resource


def get_doc_resource_by_id(id):
    g.aidocid = id
    resource = PDProtocolMetadata.query.filter(PDProtocolMetadata.id.like(str(id))).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

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
    # to get the latest record based on sponsor, protocol_number, version_number
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
            resource = db_context.session.query(PDProtocolQCSummaryData, PDProtocolMetadata.draftVersion,
                                                PDProtocolMetadata.amendment, PDProtocolMetadata.uploadDate,
                                                PDProtocolMetadata.documentFilePath,
                                                PDProtocolMetadata.projectId, PDProtocolMetadata.documentStatus,
                                                PDProtocolMetadata.protocol
                                                ).join(PDProtocolMetadata,
                                                       and_(PDProtocolQCSummaryData.aidocId == PDProtocolMetadata.id,
                                                            PDProtocolQCSummaryData.source == 'QC',
                                                            PDProtocolMetadata.qcStatus == 'QC_COMPLETED')
                                                       ).filter(text(all_filter)
                                                                ).order_by(text(order_condition)).first()
        else:
            resource = db_context.session.query(PDProtocolQCSummaryData, PDProtocolMetadata.draftVersion,
                                                PDProtocolMetadata.amendment, PDProtocolMetadata.uploadDate,
                                                PDProtocolMetadata.documentFilePath, PDProtocolMetadata.projectId,
                                                PDProtocolMetadata.documentStatus, PDProtocolMetadata.protocol,
                                                PDProtocolQCSummaryData.source,
                                                func.rank().over(partition_by=PDProtocolQCSummaryData.aidocId,
                                                                 order_by=PDProtocolQCSummaryData.source.desc()).label(
                                                    'rank')
                                                ).join(PDProtocolMetadata,
                                                       PDProtocolQCSummaryData.aidocId == PDProtocolMetadata.id
                                                       ).filter(text(all_filter)
                                                                ).order_by(text(order_condition)).all()

            resource = utils.filter_qc_status(resources=resource, qc_status=qc_status)
    except Exception as e:
        logger.error(
            f"No document resource was found in DB [Protocol: {protocol_number}; Version: {version_number}; approval_date: {approval_date}; \
            doc_id: {aidoc_id}; document_status: {document_status}; qc_status: {qc_status}]")
        logger.error(f"Exception message:\n{e}")

    return resource


def get_record_by_userid_protocol(user_id, protocol_number):
    # get record from user_protocol table on userid and protocol fields
    resource = PDUserProtocols.query.filter(PDUserProtocols.userId == user_id).filter(
        PDUserProtocols.protocol == protocol_number).all()

    return resource


def get_record_by_userid_projectid(user_id, project_id):
    # get record from user_protocol table on userid and projectid fields
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
        userprotocols.redactProfile = config.USERROLE_REDACTPROFILE_MAP.get(config.UPLOADED_USERROLE)
        try:
            db_context.session.add(userprotocols)
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            logger.error("Error while writing record to PD_user_protocol file in DB for user id: {},{}".format(
                user_id, ex))
    else:
        for record in records:
            record.isActive = True
            record.follow = True
            record.userRole = config.UPLOADED_USERROLE
            record.redactProfile = config.USERROLE_REDACTPROFILE_MAP.get(config.UPLOADED_USERROLE)
            record.lastUpdated = datetime.utcnow()
            try:
                db_context.session.merge(record)
                db_context.session.commit()
            except Exception as ex:
                db_context.session.rollback()
                logger.error(
                    "Error while updating record to PD_user_protocol file in DB for user id: {},{}".format(user_id, ex))


def get_attr_soa_details(protocol_number, aidoc_id) -> dict:
    """
    Get protocol attributes and Normalized SOA
    """
    resource = None
    resource_dict = dict()
    protocol_attributes = ""
    norm_soa = ""

    try:
        active_protocol = PDProtocolMetadata.query.filter(
            and_(PDProtocolMetadata.id == aidoc_id, PDProtocolMetadata.protocol == protocol_number,
                 PDProtocolMetadata.isActive == True)).first()
        if active_protocol is None:
            return resource_dict

    except Exception as e:
        logger.error(f"No active document found in DB [Protocol: {protocol_number}; aidoc_id: {aidoc_id}]")
        logger.error(f"Exception message:\n{e}")

    try:
        resource = Protocoldata.query.filter(Protocoldata.id == aidoc_id).first()
        if resource is not None:
            if resource.iqvdataSummary is not None:
                protocol_attributes_raw_dict = json.loads(json.loads(resource.iqvdataSummary))
                protocol_attributes = {key: value for key, value in protocol_attributes_raw_dict.items() if
                                       key in ['columns', 'data']}
            if resource.iqvdataSoaStd is not None:
                norm_soa = json.loads(json.loads(resource.iqvdataSoaStd))

            resource_dict = {'id': resource.id, 'protocolAttributes': protocol_attributes, 'normalizedSOA': norm_soa}
    except Exception as exc:
        logger.exception(
            f"Exception received while formatting the data [Protocol: {protocol_number}; aidoc_id: {aidoc_id}]. Exception: {str(exc)}")

    return resource_dict


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


def update_compare_run(compare_id):
    """
        update the compareRun i.e, how many times compare process runs for particular combination.
    """
    try:
        resource = Documentcompare.query.filter(Documentcompare.compareId == compare_id).first()
        document_compare_list = Documentcompare.query.filter(and_(Documentcompare.id1 == resource.id1,
                                                                  Documentcompare.id2 == resource.id2,
                                                                  Documentcompare.redactProfile == resource.redactProfile)).all()
        if len(document_compare_list) == 1:
            compare_run_count = 0
        else:
            compare_record = max(document_compare_list, key=lambda record: record.compareRun)
            compare_run_count = compare_record.compareRun
            compare_run_count += 1
        resource.compareRun = compare_run_count
        db_context.session.add(resource)
        db_context.session.commit()
    except Exception as exc:
        logger.exception(
            f"No Document found for [aidoc_id: {resource.id1}; compare_base_id: {resource.id2}; redact_profile: {resource.redactProfile}]. Exception: {str(exc)}")


def update_document_run_no(compare_id):
    """
        update the document run no of id1 and id2 for which comparison occurred.
    """
    try:
        resource = Documentcompare.query.filter(Documentcompare.compareId == compare_id).first()
        metadata_resource = get_doc_resource_by_id(resource.id1)
        doc1_run_no = metadata_resource.runId
        resource.doc1runId = doc1_run_no

        metadata_resource = get_doc_resource_by_id(resource.id2)
        doc2_run_no = metadata_resource.runId
        resource.doc2runId = doc2_run_no

        db_context.session.add(resource)
        db_context.session.commit()
    except Exception as exc:
        logger.exception(
            f"No Document found for [compare_id: {compare_id}].Exception: {str(exc)}")
