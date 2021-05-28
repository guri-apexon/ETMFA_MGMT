import datetime
import logging
import os
import json

from datetime import datetime

from flask import g
# from sqlalchemy import desc

from etmfa.consts import Consts as consts
from etmfa.db.db import db_context
from etmfa.db.models.documentcompare import Documentcompare
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
# from etmfa.db.models.pd_roles import PDRoles
# from etmfa.db.models.pd_users import User
# from etmfa.db.models.pd_login import Login
# from etmfa.db.models.pd_pwd_tracker import PwdTracker
from etmfa.db.models.pd_protocol_data import Protocoldata
from etmfa.db.models.pd_protocol_qcdata import Protocolqcdata
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
# from etmfa.db.models.pd_protocol_sponsor import PDProtocolSponsor
# from etmfa.db.models.pd_protocol_saved_search import PDProtocolSavedSearch
# from etmfa.db.models.pd_protocol_recent_search import PDProtocolRecentSearch
# from etmfa.db.models.pd_protocol_indications import PDProtocolIndication
# from etmfa.db.models.amp_server_run_info import amp_server_run_info
from etmfa.db.models.pd_protocol_qc_summary_data import PDProtocolQCSummaryData
from etmfa.messaging.models.processing_status import ProcessingStatus, FeedbackStatus
# from etmfa.messaging.models.document_class import DocumentClass
from etmfa.error import ManagementException
from etmfa.error import ErrorCodes
import ast
import uuid

import pandas as pd
from sqlalchemy import and_, func, or_
from sqlalchemy.sql import text
from etmfa.db import utils

logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"
NO_RESOURCE_FOUND = "No document resource is found for requested input(s): {}, {}"
ERROR_PROCESSING_STATUS = "Error while updating processing status to pd_protocol_metadata to DB for ID: {},{}"
DOCUMENT_NOT_FOUND = 'Document resource is not found for the requested input(s): {}'

# Global DB ORM object
def init_db(app):
    """ Returns db context"""

    # register database instance
    db_context.init_app(app)

    # create schema
    with app.app_context():
        # Create schema if not already created
        db_context.create_all()


def update_doc_processing_status(id: str, process_status: ProcessingStatus):
    """ Receives id for the document being processed along with percent_complete and present status of document
        If the document id being processed is present in DB, this function will update the percent_complete and
        status of document.
        If document id is not present in the DB, it will return a message saying document id not available"""

    resource = get_doc_resource_by_id(id)
    if resource is not None:
        resource.percentComplete = process_status.value
        resource.status = process_status.name

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


def received_feedbackcomplete_event(id, feedback_status: FeedbackStatus):
    resource = get_doc_status_processing_by_id(id, full_mapping=True)

    if resource is not None:
        resource.feedback = feedback_status.name
        resource.lastUpdated = datetime.utcnow()
        # log message for feedback received is updated to DB from users/reviewers
        logger.info("Feedback received for id is updated to DB: {}".format(id))
        try:
            db_context.session.commit()
            return True
        except Exception as ex:
            db_context.session.rollback()

            exception = ManagementException(id, ErrorCodes.ERROR_PROCESSING_STATUS)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error(ERROR_PROCESSING_STATUS.format(id, ex))

    return False


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
        resource.numChangesTotal = int(compare_dict.get('NumChangesTotal', '')) if compare_dict.get('NumChangesTotal','').isdigit() else 0
        resource.updatedDate = datetime.utcnow()
        db_context.session.add(resource)
        db_context.session.commit()
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(compare_dict['compare_id'], ErrorCodes.ERROR_PROTOCOL_DATA)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(
            compare_dict['compare_id'], ex))


def received_finalizationcomplete_event(id, finalattributes, message_publisher):
        finalattributes = finalattributes['db_data']
        resource = get_doc_resource_by_id(id)
        resource.isProcessing = False
        resource.isActive = True  # changed it back to true
        protocolmetadata=db_context.session.query(PDProtocolMetadata).filter(PDProtocolMetadata.id == id).first()

        protocoldata = Protocoldata()
        protocolqcdata = Protocolqcdata()
        protocolmetadata.protocolTitle = finalattributes['ProtocolTitle']
        protocolmetadata.shortTitle = finalattributes['ShortTitle']
        protocolmetadata.phase = finalattributes['phase']
        protocolmetadata.approvalDate = (None if finalattributes['approval_date'] == '' else finalattributes['approval_date'])
        protocoldata.isActive = False
        protocoldata.id = finalattributes['AiDocId']
        protocoldata.userId = finalattributes['UserId']
        protocoldata.fileName = finalattributes['SourceFileName']
        protocoldata.documentFilePath = finalattributes['documentPath']
        protocoldata.iqvdataToc = str(json.dumps(finalattributes['toc']))
        protocoldata.iqvdataSoa = str(json.dumps(finalattributes['soa']))
        protocoldata.iqvdataSummary = str(json.dumps(finalattributes['summary']))

        #Protocol qc data table updation for Backup purpose of original data
        protocolqcdata.isActive = False
        protocolqcdata.id = finalattributes['AiDocId']
        protocolqcdata.userId = finalattributes['UserId']
        protocolqcdata.fileName = finalattributes['SourceFileName']
        protocolqcdata.documentFilePath = finalattributes['documentPath']
        protocolqcdata.iqvdataToc = str(json.dumps(finalattributes['toc']))
        protocolqcdata.iqvdataSoa = str(json.dumps(finalattributes['soa']))
        #protocoldata.iqvdataSoaStd = str(json.dumps(finalattributes['iqvdataSoaStd']))
        protocolqcdata.iqvdataSummary = str(json.dumps(finalattributes['summary']))

        update_user_protocols(finalattributes['UserId'], finalattributes['ProjectId'], finalattributes['ProtocolNo'])

        # Entry in summary table
        summary_json_dict = ast.literal_eval(finalattributes['summary'])
        summary_dict = {k:v for k, v, _ in summary_json_dict['data']}
        summary_record = utils.get_updated_qc_summary_record(doc_id=id, source=config.SRC_EXTRACT, summary_dict=summary_dict, is_active_flg=True)

        try:
            db_context.session.add(protocoldata)
            db_context.session.add(protocolqcdata)
            db_context.session.add(summary_record)
            db_context.session.commit()
            update_doc_processing_status(id, ProcessingStatus.QC1)
        except Exception as ex:
            logger.error("Error while writing record to file in DB for ID: {},{}".format(id, str(ex)))
            db_context.session.rollback()
            exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
            received_documentprocessing_error_event(exception.__dict__)

        try:
            protocoldata.documentFilePath = finalattributes['documentPath']
            protocol_number = finalattributes['ProtocolNo']
            ids_compare_protocol = db_context.session.query(PDProtocolMetadata.id,
                                                            PDProtocolMetadata.protocol,
                                                            PDProtocolMetadata.documentFilePath
                                                            ).filter(
                and_(PDProtocolMetadata.protocol == protocol_number,
                     PDProtocolMetadata.id != finalattributes['AiDocId'],
                     or_(PDProtocolMetadata.status == 'QC1',
                         PDProtocolMetadata.status == 'QC2',
                         PDProtocolMetadata.status == 'PROCESS_COMPLETED'))).all()

            IQVXMLPath1 = utils.get_iqvxml_file_path(finalattributes['documentPath'], 'FIN_')
            if IQVXMLPath1:
                ids_compare_protocol_1 = list()
                for row in ids_compare_protocol:
                    IQVXMLPath2 = utils.get_iqvxml_file_path(row.documentFilePath[:row.documentFilePath.rfind('\\')], 'FIN_')
                    if IQVXMLPath2:
                        ids_compare_protocol_1.extend([{'compareId': str(uuid.uuid4()),
                                                      'id1': finalattributes['AiDocId'],
                                                      'IQVXMLPath1': IQVXMLPath1,
                                                      'id2': row.id,
                                                      'protocolNumber': protocol_number,
                                                      'IQVXMLPath2': IQVXMLPath2
                                                      },
                                                     {'compareId': str(uuid.uuid4()),
                                                      'id1': row.id,
                                                      'IQVXMLPath1': IQVXMLPath2,
                                                      'id2': finalattributes['AiDocId'],
                                                      'protocolNumber': protocol_number,
                                                      'IQVXMLPath2': IQVXMLPath1
                                                      }
                                                     ])
                ids_compare_protocol = ids_compare_protocol_1
                ret_val = add_compare_event(ids_compare_protocol, id)
                if ret_val:
                    return ids_compare_protocol

        except Exception as ex:
            logger.error("Error while creating compare json request for ID: {},{}".format(id, str(ex)))
            exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
            received_documentprocessing_error_event(exception.__dict__)


def received_documentprocessing_error_event(error_dict):
    resource = get_doc_resource_by_id(error_dict['id'])

    if resource is not None:
        # Update error status for the document
        resource.errorCode = error_dict['error_code']
        resource.errorReason = error_dict['service_name'] + error_dict['error_message']
        resource.status = "ERROR"

        resource.isProcessing = False
        resource.lastUpdated = datetime.utcnow()

        try:
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            logger.exception(
                f"Error while storing error message to pd_protocol_metadata DB table for ID: {error_dict['id'], ex}")
    else:
        logger.error(NO_RESOURCE_FOUND.format(id))

def pd_fetch_summary_data(aidocid, userid):
    try:
        resource = Protocoldata.query.filter(Protocoldata.id == aidocid).first()
        if resource:
            summary = ast.literal_eval(json.loads(resource.iqvdataSummary))
            summary_dict = {k:v for k, v, _ in summary['data']}
        else:
            return None

        summary_record = utils.get_updated_qc_summary_record(doc_id=aidocid, source=config.SRC_QC, summary_dict=summary_dict, is_active_flg=True, qc_approved_by=userid)            
        db_context.session.merge(summary_record)
        db_context.session.commit()
        return aidocid
    except Exception as ex:
        logger.error(ERROR_PROCESSING_STATUS.format(aidocid, str(ex)))
        db_context.session.rollback()
        exception = ManagementException(aidocid, ErrorCodes.ERROR_QC_SUMMARY_DATA)
        received_documentprocessing_error_event(exception.__dict__)



def save_doc_processing(request, _id, doc_path, draftVersion):
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
    resource.draftVersion = draftVersion
    resource.percentComplete = ProcessingStatus.TRIAGE_STARTED.value
    resource.status = ProcessingStatus.TRIAGE_STARTED.name


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


def get_doc_processed_by_id(id, full_mapping=True):
    resource_dict = get_doc_attributes_by_id(id)

    return resource_dict


def get_doc_proc_metrics_by_id(id, full_mapping=True):
    resource_dict = get_doc_metrics_by_id(id)

    return resource_dict

def get_file_contents_by_id(protocol_number:str, aidoc_id:str, protocol_number_verified:bool = False) -> str:
    """
    Extracts file toc json by aidoc_id
    
    If protocol_number and aidoc_id are already verified, then extract contents directly from data.
        If not verified by joining with metadata table before extracting contents 
    """
    cleaned_inputs = utils.clean_inputs(protocol_number=protocol_number, aidoc_id=aidoc_id)
    protocol_number = cleaned_inputs.get('protocol_number', '')
    aidoc_id = cleaned_inputs.get('aidoc_id', '')
    
    try:
        if protocol_number_verified:
            where_clause = f"id = '{aidoc_id}' AND isActive = 1"
            resource = db_context.session.query(Protocoldata.id, Protocoldata.iqvdataToc
                                                       ).filter(text(where_clause)
                                                       ).first()
        else:
            resource = db_context.session.query(Protocoldata.id, Protocoldata.iqvdataToc
                                                   ).join(PDProtocolMetadata, and_(PDProtocolMetadata.id == Protocoldata.id, 
                                                        PDProtocolMetadata.protocol == protocol_number, Protocoldata.id == aidoc_id, Protocoldata.isActive == 1)
                                                        ).first()
                             
        if resource:
            result = resource[1]
        else:
            result = None
    except Exception as e:
        logger.error(NO_RESOURCE_FOUND.format(aidoc_id))
        result = None
    return result

def get_compare_documents(base_doc_id, compare_doc_id):
    basedocid = base_doc_id
    comparedocid = compare_doc_id
    resource_IQVdata = None
    resource = Documentcompare.query.filter(Documentcompare.id1 == basedocid, Documentcompare.id2 == comparedocid).first()
    flag_order=1
    if resource is None:
        resource = Documentcompare.query.filter(Documentcompare.id1 == comparedocid,
                                                Documentcompare.id2 == basedocid).first()
        flag_order=-1


    else:
        None
    #to check none
    if resource is not None:
        resource_IQVdata = resource.iqvdata
    else:
        logger.error(NO_RESOURCE_FOUND.format(basedocid, comparedocid))

    return resource_IQVdata

def get_doc_metrics_by_id(id):
    g.aidocid = id
    resource = Metric.query.filter(Metric.id.like(str(id))).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return resource


def get_doc_status_processing_by_id(id, full_mapping=True):
    resource_dict = get_doc_resource_by_id(id)

    return resource_dict

def get_compare_resource_by_compare_id(comparevalues):
    compareid = comparevalues['COMPARE_ID']
    resource = Documentcompare.query.filter(Documentcompare.compareId == compareid).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(compareid))
    return resource

def get_doc_resource_by_id(id):
    g.aidocid = id
    resource = PDProtocolMetadata.query.filter(PDProtocolMetadata.id.like(str(id))).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return resource

def get_user_protocol_by_id(id):
    g.aidocid = id
    resource = PDUserProtocols.query.filter(PDUserProtocols.id.like(str(id))).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return resource

def upsert_attributevalue(doc_processing_id, namekey, value):
    g.aidocid = id
    doc_processing_resource = get_doc_attributes_by_id(doc_processing_id)

    if doc_processing_resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))
    else:
        try:
            setattr(doc_processing_resource, namekey, value)
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            exception = ManagementException(id, ErrorCodes.ERROR_UPDATING_ATTRIBUTES)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error("Error while updating attribute to PD_protocol_data to DB for ID: {},{}".format(
                doc_processing_id, ex))


def get_attribute_dict(doc_processing_id):
    doc_processing_resource = get_doc_resource_by_id(doc_processing_id)

    if doc_processing_resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return doc_processing_resource


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
                                               PDProtocolMetadata.versionNumber == version_number).order_by(PDProtocolMetadata.timeCreated.desc()).first()

    return resource

def set_draft_version(document_status, sponsor, protocol, version_number):
    # to set draft version for documents
    if not version_number:
        version_number = '-0.01'

    if document_status == 'draft':
        resource = get_latest_record(sponsor, protocol, version_number)

        if resource is None:
            draftVersion = float(version_number) + 0.01
        else:
            if resource.documentStatus == 'draft':
                old_draftVersion = resource.draftVersion
                draftVersion = float(old_draftVersion) + 0.01
            else:
                draftVersion = float(version_number) + 0.01
    else:
        draftVersion = None
    return draftVersion 

def get_latest_protocol(protocol_number, version_number="", approval_date="", aidoc_id="", document_status="", qc_status="", is_top_1_only=True):
    """
    Get top-1 or all the protocol based on input arguments
    """
    resource = None
    
    # Get dynamic conditions
    all_filter, order_condition = utils.get_filter_conditions(protocol_number, version_number, approval_date, aidoc_id, document_status)
        
    try:
        if is_top_1_only:
            resource = db_context.session.query(PDProtocolQCSummaryData, PDProtocolMetadata.draftVersion, PDProtocolMetadata.amendment, PDProtocolMetadata.uploadDate, PDProtocolMetadata.documentFilePath,
                                                PDProtocolMetadata.projectId, PDProtocolMetadata.documentStatus, PDProtocolMetadata.protocol
                                                   ).join(PDProtocolMetadata, and_(PDProtocolQCSummaryData.aidocId == PDProtocolMetadata.id, PDProtocolQCSummaryData.source == 'QC')
                                                   ).filter(text(all_filter)
                                                   ).order_by(text(order_condition)).first()
           
        else:
            resource = db_context.session.query(PDProtocolQCSummaryData, PDProtocolMetadata.draftVersion, PDProtocolMetadata.amendment, PDProtocolMetadata.uploadDate, PDProtocolMetadata.documentFilePath,
                                                PDProtocolMetadata.projectId, PDProtocolMetadata.documentStatus, PDProtocolMetadata.protocol,
                                                PDProtocolQCSummaryData.source,
                                                func.rank().over(partition_by = PDProtocolQCSummaryData.aidocId, order_by = PDProtocolQCSummaryData.source.desc()).label('rank')
                                                   ).join(PDProtocolMetadata, PDProtocolQCSummaryData.aidocId == PDProtocolMetadata.id
                                                   ).filter(text(all_filter)
                                                   ).order_by(text(order_condition)).all()
            
            resource = utils.filter_qc_status(resources = resource, qc_status = qc_status)
    except Exception as e:
        logger.error(f"No document resource was found in DB [Protocol: {protocol_number}; Version: {version_number}; approval_date: {approval_date}; \
            doc_id: {aidoc_id}; document_status: {document_status}; qc_status: {qc_status}]")
        logger.error(f"Exception message:\n{e}")
    
    return resource


def get_record_by_userid_protocol(user_id, protocol_number):
    # get record from user_protocol table on userid and protocol fields
    resource = PDUserProtocols.query.filter(PDUserProtocols.userId == user_id).filter(PDUserProtocols.protocol == protocol_number).all()

    return resource

def get_record_by_userid_projectid(user_id, project_id):
    # get record from user_protocol table on userid and projectid fields
    resource = PDUserProtocols.query.filter(PDUserProtocols.userId == user_id, PDUserProtocols.projectId == project_id).all()

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
            record.userRole = "primary"
            record.lastUpdated = datetime.utcnow()
            try:
                db_context.session.merge(record)
                db_context.session.commit()
            except Exception as ex:
                db_context.session.rollback()
                logger.error("Error while updating record to PD_user_protocol file in DB for user id: {},{}".format(user_id, ex))
