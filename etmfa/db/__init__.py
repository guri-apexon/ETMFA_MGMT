import datetime
import logging
import os
import json

from datetime import datetime

from flask import g
from sqlalchemy import desc

from etmfa.consts import Consts as consts
from etmfa.db.db import db_context
from etmfa.db.models.documentcompare import Documentcompare
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_roles import PDRoles
from etmfa.db.models.pd_users import User
from etmfa.db.models.pd_login import Login
from etmfa.db.models.pd_pwd_tracker import PwdTracker
from etmfa.db.models.pd_protocol_data import Protocoldata
from etmfa.db.models.pd_protocol_qcdata import Protocolqcdata
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_protocol_sponsor import PDProtocolSponsor
from etmfa.db.models.pd_protocol_saved_search import PDProtocolSavedSearch
from etmfa.db.models.pd_protocol_recent_search import PDProtocolRecentSearch
from etmfa.db.models.pd_protocol_indications import PDProtocolIndication
from etmfa.db.models.amp_server_run_info import amp_server_run_info
from etmfa.db.models.pd_protocol_qc_summary_data import PDProtocolQCSummaryData
from etmfa.messaging.models.processing_status import ProcessingStatus, FeedbackStatus
from etmfa.messaging.models.document_class import DocumentClass
from etmfa.error import ManagementException
from etmfa.error import ErrorCodes
import ast

import pandas as pd
from sqlalchemy import and_
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


def add_compare_event(compare_req_msg, protocol_number, project_id, protocol_number2, project_id2, user_id):
    compare = Documentcompare()
    compare.compareId = compare_req_msg['COMPARE_ID']
    compare.id1 = compare_req_msg['BASE_DOC_ID']
    compare.protocolNumber = protocol_number
    compare.projectId = project_id
    compare.id2 = compare_req_msg['COMPARE_DOC_ID']
    compare.protocolNumber2 = protocol_number2
    compare.projectId2 = project_id2
    compare.userId = user_id
    compare.baseIqvXmlPath = compare_req_msg['BASE_IQVXML_PATH']
    compare.compareIqvXmlPath = compare_req_msg['COMPARE_IQVXML_PATH']
    compare.requestType = compare_req_msg['REQUEST_TYPE']
    try:
        db_context.session.add(compare)
        db_context.session.commit()
        return compare_req_msg
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(
            compare['compare_id'], ex))

def insert_compare(comparevalues,comparedata,UPDATED_IQVXML_PATH):

    resource = Documentcompare()
    resource.id1=comparevalues[0]
    resource.protocolNumber=comparevalues[1]
    resource.projectId=comparevalues[2]
    resource.versionNumber=comparevalues[3]
    resource.amendmentNumber=comparevalues[4]
    resource.documentStatus=comparevalues[5]
    resource.id2=comparevalues[6]
    resource.protocolNumber2=comparevalues[7]
    resource.projectId2=comparevalues[8]
    resource.versionNumber2=comparevalues[9]
    resource.amendmentNumber2=comparevalues[10]
    resource.documentStatus2=comparevalues[11]
    resource.updatedIqvXmlPath=UPDATED_IQVXML_PATH
    resource.iqvdata=str(json.dumps(comparedata))
    resource.similarityScore=comparevalues[12]
    try:
        db_context.session.add(resource)
        db_context.session.commit()
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(
            comparevalues['compare_id'], ex))


def received_comparecomplete_event(msg_comparevalues, message_publisher):
    if msg_comparevalues['ALL_COMPARISONS']:
        for comparevalues,comparedata in msg_comparevalues['ALL_COMPARISONS'].items():
            insert_compare(ast.literal_eval(comparevalues),comparedata,msg_comparevalues['UPDATED_IQVXML_PATH'])
    else:
        logger.warning('No values to compare. Moving to Finalization')

def received_finalizationcomplete_event(id, finalattributes, message_publisher):
        finalattributes = finalattributes['db_data']
        resource = get_doc_resource_by_id(id)
        resource.isProcessing = False
        resource.isActive = True  # changed it back to true
        protocolmetadata=db_context.session.query(PDProtocolMetadata).filter(PDProtocolMetadata.id == id).first()

        protocoldata = Protocoldata()
        protocolqcdata = Protocolqcdata()
        #protocolmetadata = PDProtocolMetadata()
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
        #protocoldata.iqvdataSoaStd = str(json.dumps(finalattributes['iqvdataSoaStd']))
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

        try:
            db_context.session.add(protocoldata)
            db_context.session.add(protocolqcdata)
            db_context.session.commit()
            update_doc_processing_status(id, ProcessingStatus.QC1)
        except Exception as ex:
            db_context.session.rollback()
            exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error("Error while writing record to file in DB for ID: {},{}".format(
                finalattributes['AiDocId'], ex))


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
            for row in summary['data']:
                summary[row[0]]=row[1]
        else:
            return None

        protocolqcsummary = PDProtocolQCSummaryData()
        protocolqcsummary.aidocId = aidocid
        protocolqcsummary.source = 'QC'
        protocolqcsummary.sponsor = summary['sponsor']
        protocolqcsummary.protocolNumber = summary['protocol_number']
        protocolqcsummary.trialPhase = summary['trial_phase']
        protocolqcsummary.versionNumber = summary['version_number']
        protocolqcsummary.approvalDate = summary['approval_date']
        protocolqcsummary.versionDate = summary['version_date']
        protocolqcsummary.protocolTitle = summary['protocol_title']
        protocolqcsummary.protocolShortTitle = summary['protocol_title_short']
        protocolqcsummary.indications = summary['indication']
        protocolqcsummary.isActive = True
        protocolqcsummary.moleculeDevice = summary['molecule_device']
        protocolqcsummary.investigator = summary['investigator']
        protocolqcsummary.blinded = summary['blinded']
        protocolqcsummary.drug = summary['drug']
        protocolqcsummary.compoundNumber = summary['compound_number']
        protocolqcsummary.control = summary['control']
        protocolqcsummary.endPoints = summary['endpoints']
        protocolqcsummary.trialTypeRandomized = summary['trial_type_randomized']
        protocolqcsummary.numberOfSubjects = summary['number_of_subjects']
        protocolqcsummary.participantAge = summary['participant_age']
        protocolqcsummary.participantSex = summary['participant_sex']
        protocolqcsummary.studyPopulation = summary['study_population']
        protocolqcsummary.inclusionCriteria = summary['inclusion_criteria']
        protocolqcsummary.exclusionCriteria = summary['exclusion_criteria']
        protocolqcsummary.primaryObjectives = summary['primary_objectives']
        protocolqcsummary.secondaryObjectives = summary['secondary_objectives']
        protocolqcsummary.qcApprovedBy = userid
        protocolqcsummary.timeCreated = datetime.now()
        protocolqcsummary.timeUpdated = datetime.now()

        db_context.session.merge(protocolqcsummary)
        db_context.session.commit()
        return aidocid
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_SAVING)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error(ERROR_PROCESSING_STATUS.format(aidocid, ex))



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

def get_latest_protocol(protocol_number, version_number="", approval_date="", aidoc_id="", document_status="", is_top_1_only=True):
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
                                                PDProtocolMetadata.projectId, PDProtocolMetadata.documentStatus, PDProtocolMetadata.protocol
                                                   ).join(PDProtocolMetadata, and_(PDProtocolQCSummaryData.aidocId == PDProtocolMetadata.id, PDProtocolQCSummaryData.source == 'QC')
                                                   ).filter(text(all_filter)
                                                   ).order_by(text(order_condition)).all()
            
    except Exception as e:
        logger.error(f"No document resource was found in DB [Protocol: {protocol_number}; Version: {version_number}; approval_date: {approval_date}; doc_id: {aidoc_id}; document_status: {document_status}]")
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
            if record.isActive == False:
                record.isActive = True
            else:
                continue
            try:
                db_context.session.commit()
            except Exception as ex:
                db_context.session.rollback()
                logger.error("Error while updating record to PD_user_protocol file in DB for user id: {},{}".format(user_id, ex))
