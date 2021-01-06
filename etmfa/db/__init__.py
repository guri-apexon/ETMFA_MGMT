import datetime
import logging
import os
import json
from datetime import datetime

from filehash import FileHash
from flask import g
from sqlalchemy import desc

from etmfa.consts import Consts as consts
from etmfa.db.db import db_context
from etmfa.db.models.documentcompare import Documentcompare
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_roles import PDRoles
from etmfa.db.models.pd_users import PDUsers
from etmfa.db.models.pd_protocol_data import Protocoldata
from etmfa.db.models.pd_protocol_sponsor import PDProtocolSponsor
from etmfa.db.models.pd_protocol_saved_search import PDProtocolSavedSearch
from etmfa.db.models.pd_protocol_recent_search import PDProtocolRecentSearch
from etmfa.db.models.pd_protocol_indications import PDProtocolIndication
from etmfa.db.models.amp_server_run_info import amp_server_run_info
from etmfa.messaging.models.processing_status import ProcessingStatus, FeedbackStatus
from etmfa.messaging.models.document_class import DocumentClass
from etmfa.error import ManagementException
from etmfa.error import ErrorCodes



logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"
NO_RESOURCE_FOUND = "No document resource was found in DB for ID: {}"
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
    compare.id = compare_req_msg['BASE_DOC_ID']
    compare.protocolNumber = protocol_number
    compare.projectId = project_id
    # compare.version_number = compare_req_msg['']#these will added if additional details are made mandatory
    # compare.amendment_number = compare_req_msg['']#these will added if additional details are made mandatory
    # compare.document_status = compare_req_msg['']#these will added if additional details are made mandatory
    compare.id2 = compare_req_msg['COMPARE_DOC_ID']
    compare.protocolNumber2 = protocol_number2
    compare.projectId2 = project_id2
    # compare.version_number2 = compare_req_msg['']#these will added if additional details are made mandatory
    # compare.amendment_number2 = compare_req_msg['']#these will added if additional details are made mandatory
    # compare.document_status2 = compare_req_msg['']#these will added if additional details are made mandatory
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

def received_comparecomplete_event(comparevalues, message_publisher):
    resource = Documentcompare.query.filter(Documentcompare.compareId == comparevalues['COMPARE_ID']).first()
    if resource is not None:
        resource.similarityScore = comparevalues['SIMILARITY_SCORE']
        resource.updatedIqvXmlPath = comparevalues['UPDATED_BASE_IQVXML_PATH']
        resource.iqvdata = str(comparevalues['IQVDATA'])
    try:
        db_context.session.commit()
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(
            comparevalues['compare_id'], ex))


def received_finalizationcomplete_event(id, finalattributes, message_publisher):
    if update_doc_processing_status(id, ProcessingStatus.PROCESS_COMPLETED):

        resource = get_doc_resource_by_id(id)
        resource.isProcessing = False
        resource.isActive = True

        resource2 = get_user_protocol_by_id(id)
        resource.isActive = True


        protocoldata = Protocoldata()
        
        finalattributes = finalattributes['db_data']
        protocoldata.id = finalattributes['AiDocId']
        protocoldata.userId = finalattributes['UserId']
        protocoldata.fileName = finalattributes['SourceFileName']
        protocoldata.documentFilePath = finalattributes['documentPath']
        protocoldata.iqvdataToc = str(json.dumps(finalattributes['toc']))
        protocoldata.iqvdataSoa = str(json.dumps(finalattributes['soa']))
        #protocoldata.iqvdataSoaStd = str(json.dumps(finalattributes['iqvdataSoaStd']))
        protocoldata.iqvdataSummary = str(json.dumps(finalattributes['summary']))

        try:
            db_context.session.add(protocoldata)
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            exception = ManagementException(id, ErrorCodes.ERROR_PROTOCOL_DATA)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error("Error while writing record to PD_document_attributes file in DB for ID: {},{}".format(
                finalattributes['id'], ex))


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

    resource2 = PDUserProtocols.from_post_request(request, _id, doc_path)
    resource2.userId = request['userId']
    resource2.protocol = request['protocolNumber']

    try:
        db_context.session.add(resource)
        db_context.session.add(resource2)
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

def get_doc_processed_by_protocolnumber(id, protocol_number, project_id, doc_status):
    resource_dict = get_doc_attributes_by_protocolnumber(id, protocol_number, project_id, doc_status)
    return resource_dict



def get_doc_proc_metrics_by_id(id, full_mapping=True):
    resource_dict = get_doc_metrics_by_id(id)

    return resource_dict


def get_doc_attributes_by_id(id):
    g.aidocid = id
    resource = Documentattributes.query.filter(Documentattributes.id.like(str(id))).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return resource
#

def fetch_compare_id(id, protocol_number, project_id, doc_status):
    documentid = id
    protocolnumber = protocol_number
    projectid = project_id
    docstatus = doc_status
    # to check the correct values are only extracted
    resource = Documentattributes.query.filter(Documentattributes.id == documentid,
                                               Documentattributes.protocolNumber == protocolnumber,
                                               Documentattributes.projectId == projectid,
                                               Documentattributes.documentStatus == docstatus).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return resource




def get_doc_attributes_by_protocolnumber(id, protocol_number, project_id, doc_status):
    documentid = id
    protocolnumber = protocol_number
    projectid = project_id
    docstatus = doc_status
    # to check the correct values are only extracted
    resource = Documentattributes.query.filter(Documentattributes.id == documentid,
                                               Documentattributes.protocolNumber == protocolnumber,
                                               Documentattributes.projectId == projectid,
                                               Documentattributes.documentStatus == docstatus).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return resource



def get_mcra_attributes_by_protocolnumber(protocol_number, doc_status = 'final'):
    protocolnumber = protocol_number
    docstatus = doc_status
    # to check the correct values are only extracted
    resource = Documentattributes.query.filter(Documentattributes.protocolNumber == protocolnumber,
                                               Documentattributes.documentStatus == docstatus).order_by(desc(Documentattributes.versionNumber)).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return resource


def get_compare_documents_validation(protocol_number, project_id, document_id, protocol_number2, project_id2,
                                             document_id2, request_type):
    protocolnumber = protocol_number
    projectid = project_id
    docid = document_id
    protocolnumber2 = protocol_number2
    projectid2 = project_id2
    docid2 = document_id2
    requesttype = request_type
    # to check the correct values are only extracted
    resource = Documentcompare.query.filter(Documentcompare.protocolNumber == protocolnumber,
                                            Documentcompare.projectId == projectid,
                                            Documentcompare.id1 == docid,
                                            Documentcompare.protocolNumber2 == protocolnumber2,
                                            Documentcompare.projectId2 == projectid2,
                                            Documentcompare.id2 == docid2,
                                            Documentcompare.requestType == requesttype).first()
    # if resource is None:
    #     logger.error(NO_RESOURCE_FOUND.format())
    return resource


def get_compare_documents(compare_id):
    compareid = compare_id
    resource_IQVdata = None
    resource = Documentcompare.query.filter(Documentcompare.compareId == compareid).first()
    #to check none
    if resource is not None:
        resource_IQVdata = resource.iqvdata
    else:
        logger.error(NO_RESOURCE_FOUND.format(compare_id))
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
