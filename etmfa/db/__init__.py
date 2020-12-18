import datetime
import logging
import os
from datetime import datetime

from filehash import FileHash
from flask import g
from sqlalchemy import desc

from etmfa.consts import Consts as consts
from etmfa.db.db import db_context
from etmfa.db.models.documentProcess import DocumentProcess
from etmfa.db.models.documentattributes import Documentattributes
from etmfa.db.models.documentcompare import Documentcompare
from etmfa.db.models.documentduplicate import Documentduplicate
from etmfa.db.models.documentfeedback import Documentfeedback
from etmfa.db.models.metric import Metric
from etmfa.messaging.models.processing_status import ProcessingStatus, FeedbackStatus
from etmfa.messaging.models.document_class import DocumentClass
from etmfa.error import ManagementException
from etmfa.error import ErrorCodes

logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"
NO_RESOURCE_FOUND = "No document resource was found in DB for ID: {}"
ERROR_PROCESSING_STATUS = "Error while updating processing status to PD_document_process to DB for ID: {},{}"


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
    compare.compare_id = compare_req_msg['COMPARE_ID']
    compare.doc_id = compare_req_msg['BASE_DOC_ID']
    compare.protocol_number = protocol_number
    compare.project_id = project_id
    # compare.version_number = compare_req_msg['']#these will added if additional details are made mandatory
    # compare.amendment_number = compare_req_msg['']#these will added if additional details are made mandatory
    # compare.document_status = compare_req_msg['']#these will added if additional details are made mandatory
    compare.doc_id2 = compare_req_msg['COMPARE_DOC_ID']
    compare.protocol_number2 = protocol_number2
    compare.project_id2 = project_id2
    # compare.version_number2 = compare_req_msg['']#these will added if additional details are made mandatory
    # compare.amendment_number2 = compare_req_msg['']#these will added if additional details are made mandatory
    # compare.document_status2 = compare_req_msg['']#these will added if additional details are made mandatory
    compare.user_id = user_id
    compare.base_IQV_xml_path = compare_req_msg['BASE_IQVXML_PATH']
    compare.compare_IQV_xml_path = compare_req_msg['COMPARE_IQVXML_PATH']
    compare.request_type = compare_req_msg['REQUEST_TYPE']
    try:
        db_context.session.add(compare)
        db_context.session.commit()
        return compare_req_msg
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_ATTRIBUTES)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(
            compare['compare_id'], ex))

def received_comparecomplete_event(comparevalues, message_publisher):
    resource = Documentcompare.query.filter(Documentcompare.compare_id == comparevalues['COMPARE_ID']).first()
    if resource is not None:
        resource.similarity_score = comparevalues['SIMILARITY_SCORE']
        resource.updated_IQV_xml_path = comparevalues['UPDATED_BASE_IQVXML_PATH']
        resource.iqvdata = str(comparevalues['IQVDATA']).encode('UTF-8')
    try:
        db_context.session.commit()
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_ATTRIBUTES)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to PD_document_compare file in DB for ID: {},{}".format(
            comparevalues['compare_id'], ex))


def received_finalizationcomplete_event(id, finalattributes, message_publisher):
    if update_doc_processing_status(id, ProcessingStatus.PROCESS_COMPLETED):

        resource = get_doc_resource_by_id(id)
        resource.isProcessing = False

        metrics = Metric(id)
        metrics.id = finalattributes['id']
        metrics.totalProcessTime = finalattributes['total_process_time']
        metrics.queueWaitTime = finalattributes['queue_wait_time']
        metrics.triageMachineName = finalattributes['triage_machine_name']
        metrics.triageVersion = finalattributes['triage_version']
        metrics.triageStartTime = finalattributes['triage_start_time']
        metrics.triageEndTime = finalattributes['triage_end_time']
        metrics.triageProcTime = finalattributes['triage_proc_time']
        metrics.digitizerMachineName = finalattributes['digitizer_machine_name']
        metrics.digitizerVersion = finalattributes['digitizer_version']
        metrics.digitizerStartTime = finalattributes['digitizer_start_time']
        metrics.digitizerEndTime = finalattributes['digitizer_end_time']
        metrics.digitizerProcTime = finalattributes['digitizer_proc_time']
        metrics.classificationMachineName = finalattributes['classification_machine_name']
        metrics.classificationVersion = finalattributes['classification_version']
        metrics.classificationStartTime = finalattributes['classification_start_time']
        metrics.classificationEndTime = finalattributes['classification_end_time']
        metrics.classificationProcTime = finalattributes['classification_proc_time']
        metrics.attExtractionMachineName = finalattributes['att_extraction_machine_name']
        metrics.attExtractionVersion = finalattributes['att_extraction_version']
        metrics.attExtractionStartTime = finalattributes['att_extraction_start_time']
        metrics.attExtractionEndTime = finalattributes['att_extraction_end_time']
        metrics.attExtractionProcTime = finalattributes['att_extraction_proc_time']
        metrics.finalizationMachineName = finalattributes['finalization_machine_name']
        metrics.finalizationVersion = finalattributes['finalization_version']
        metrics.finalizationStartTime = finalattributes['finalization_start_time']
        metrics.finalizationEndTime = finalattributes['finalization_end_time']
        metrics.finalizationProcTime = finalattributes['finalization_proc_time']
        metrics.docType = finalattributes['doc_type']
        metrics.docTypeOriginal = finalattributes['doc_type_original']
        metrics.docSegments = finalattributes['doc_segments']
        metrics.docPages = finalattributes['doc_pages']

        attributes = Documentattributes()
        attributes.id = finalattributes['id']
        attributes.userId = resource.userId
        attributes.fileName = safe_unicode(resource.fileName)
        attributes.documentFilePath = resource.documentFilePath
        attributes.customer = safe_unicode(finalattributes['customer'])
        attributes.protocol = safe_unicode(finalattributes['protocol'])
        attributes.country = safe_unicode(finalattributes['country'])
        attributes.site = safe_unicode(finalattributes['site'])
        attributes.docClass = finalattributes['doc_class']
        attributes.priority = finalattributes['priority']
        attributes.receivedDate = finalattributes['received_date']
        # TODO:Storing site_personnel_list in DB
        attributes.sitePersonnelList = safe_unicode(finalattributes['site_personnel_list'])
        attributes.tmfEnvironment = finalattributes['tmf_environment']
        attributes.tmfIbr = finalattributes['tmf_ibr']

        attributes.docCompConf = finalattributes['doc_comp_conf']
        attributes.docClassification = finalattributes['doc_classification']
        attributes.docClassificationConf = finalattributes['doc_classification_conf']
        attributes.docDate = finalattributes['doc_date']
        attributes.docDateConf = finalattributes['doc_date_conf']
        attributes.docDateType = finalattributes['doc_date_type']
        attributes.name = safe_unicode(finalattributes['name'])
        attributes.nameConf = finalattributes['name_conf']
        attributes.language = finalattributes['language']
        attributes.languageConf = finalattributes['language_conf']
        attributes.subject = safe_unicode(finalattributes['subject'])
        attributes.subjectConf = finalattributes['subject_conf']
        attributes.alcoacCheckError = finalattributes['alcoac_check_error']
        attributes.alcoacCheckCompScore = finalattributes['alcoac_check_comp_score']
        attributes.alcoacCheckCompScoreConf = finalattributes['alcoac_check_comp_score_conf']
        attributes.docSubclassification = finalattributes['doc_subclassification']
        attributes.docSubclassificationConf = finalattributes['doc_subclassification_conf']
        attributes.docClassificationElvis = finalattributes['doc_classification_elvis']
        attributes.unblinded = finalattributes['blinded']

        try:
            db_context.session.add(attributes)
            db_context.session.add(metrics)
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_ATTRIBUTES)
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
                f"Error while storing error message to PD_document_process DB table for ID: {error_dict['id'], ex}")
    else:
        logger.error(NO_RESOURCE_FOUND.format(id))


def save_doc_feedback(_id, feedbackdata):
    recordfound = get_doc_resource_by_id(_id)

    resourcefb = Documentfeedback()

    resourcefb.p_id = str(int((datetime.now().timestamp()) * 1000000))
    resourcefb.id = feedbackdata['id']
    resourcefb.fileName = safe_unicode(recordfound.fileName)
    resourcefb.documentFilePath = recordfound.documentFilePath
    resourcefb.userId = feedbackdata['userId']
    resourcefb.feedbackSource = feedbackdata['feedbackSource']
    resourcefb.customer = safe_unicode(feedbackdata['customer'])
    resourcefb.protocol = safe_unicode(feedbackdata['protocol'])
    resourcefb.country = safe_unicode(feedbackdata['country'])
    resourcefb.site = safe_unicode(feedbackdata['site'])
    resourcefb.documentClass = feedbackdata['documentClass']
    resourcefb.documentDate = feedbackdata['documentDate']
    resourcefb.documentClassification = feedbackdata['documentClassification']
    resourcefb.name = safe_unicode(feedbackdata['name'])
    resourcefb.language = feedbackdata['language']
    resourcefb.documentRejected = feedbackdata['documentRejected']
    resourcefb.attributeAuxillaryList = safe_unicode(str(feedbackdata['attributeAuxillaryList']))

    try:
        db_context.session.add(resourcefb)
        db_context.session.commit()
    except Exception as ex:
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_FEEDBACK)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to etmfa_document_feedback file in DB for ID: {},{}".format(_id, ex))

    return resourcefb.as_dict()


def save_doc_processing_duplicate(request, _id, file_name, doc_path):
    resource = Documentduplicate()

    sha512hasher = FileHash('sha512')
    resource.id = _id
    resource.userId = request['userId'] if request['userId'] is not None else ''
    resource.site = safe_unicode(request['site']) if request['site'] is not None else ''
    resource.fileName = safe_unicode(file_name)
    resource.docHash = sha512hasher.hash_file(doc_path)
    resource.documentFilePath = doc_path
    resource.customer = safe_unicode(request['customer']) if request['customer'] is not None else ''
    resource.protocol = safe_unicode(request['protocol']) if request['protocol'] is not None else ''
    resource.country = safe_unicode(request['country']) if request['country'] is not None else ''
    resource.site = safe_unicode(request['site']) if request['site'] is not None else ''
    resource.documentClass = request['documentClass'] if request['documentClass'] is not None else ''
    resource.receivedDate = request['receivedDate'] if request['receivedDate'] is not None else ''

    resourcefound = get_doc_duplicate_by_id(resource)
    duplicateresource = ' '

    if resourcefound is None:
        resource.docDuplicateFlag = 0

        try:
            db_context.session.add(resource)
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            exception = ManagementException(_id, ErrorCodes.ERROR_DOCUMENT_DUPLICATE)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error(
                "Error while writing record to pd_document_duplicate file in DB for ID: {},{}".format(_id, ex))

    else:
        duplicateresource = resourcefound.id
        user_id = resourcefound.userId
        time_created = resourcefound.timeCreated
        logger.info("Document previously uploaded by user: {} at time {} with file name {} having id {}".format(user_id, time_created, file_name, duplicateresource))
        doc_duplicate_flag_update = resourcefound.docDuplicateFlag + 1
        last_updated = datetime.utcnow()
        setattr(resourcefound, 'docDuplicateFlag', doc_duplicate_flag_update)
        setattr(resourcefound, 'lastUpdated', last_updated)

        try:
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            exception = ManagementException(_id, ErrorCodes.ERROR_UPDATING_ATTRIBUTES)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error(
                "Error while writing record to PD_document_duplicate file in DB for ID: {},{}".format(_id, ex))

    return duplicateresource


def get_doc_duplicate_by_id(resourcechk, full_mapping=False):
    base_query = Documentduplicate.query.filter(Documentduplicate.docHash == resourcechk.docHash,
                                               Documentduplicate.customer == resourcechk.customer,
                                               Documentduplicate.protocol == resourcechk.protocol,
                                               Documentduplicate.documentClass == resourcechk.documentClass.lower(),
                                               Documentduplicate.documentRejected == False)

    if resourcechk.documentClass.lower() == DocumentClass.CORE.value:
        resource = base_query.first()

    elif resourcechk.documentClass.lower() == DocumentClass.COUNTRY.value:
        resource = base_query.filter(Documentduplicate.country == resourcechk.country).first()

    elif resourcechk.documentClass.lower() == DocumentClass.SITE.value:
        resource = base_query.filter(Documentduplicate.country == resourcechk.country,
                                     Documentduplicate.site == resourcechk.site).first()
    else:
        resource = None

    return resource


def save_doc_processing(request, _id, doc_path):
    resource = DocumentProcess.from_post_request(request, _id, doc_path)

    resource.documentFilePath = doc_path
    resource.userId = request['userId']
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

def fetch_comparae_id(id, protocol_number, project_id, doc_status):
    documentid = id
    protocolnumber = protocol_number
    projectid = project_id
    docstatus = doc_status
    # to check the correct values are only extracted
    resource = Documentattributes.query.filter(Documentattributes.id == documentid,
                                               Documentattributes.protocol_number == protocolnumber,
                                               Documentattributes.project_id == projectid,
                                               Documentattributes.document_status == docstatus).first()

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
                                               Documentattributes.protocol_number == protocolnumber,
                                               Documentattributes.project_id == projectid,
                                               Documentattributes.document_status == docstatus).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

    return resource



def get_mcra_attributes_by_protocolnumber(protocol_number, doc_status = 'active'):
    protocolnumber = protocol_number
    docstatus = doc_status
    # to check the correct values are only extracted
    resource = Documentattributes.query.filter(Documentattributes.protocol_number == protocolnumber,
                                               Documentattributes.document_status == docstatus).order_by(desc(Documentattributes.version_number)).first()

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
    resource = Documentcompare.query.filter(Documentcompare.protocol_number == protocolnumber,
                                            Documentcompare.project_id == projectid,
                                            Documentcompare.doc_id == docid,
                                            Documentcompare.protocol_number2 == protocolnumber2,
                                            Documentcompare.project_id2 == projectid2,
                                            Documentcompare.doc_id2 == docid2,
                                            Documentcompare.request_type == requesttype).first()
    # if resource is None:
    #     logger.error(NO_RESOURCE_FOUND.format())
    return resource


def get_compare_documents(compare_id):
    compareid = compare_id
    resource = Documentcompare.query.filter(Documentcompare.compare_id == compareid).first()
    try:
        resource = eval(resource.iqvdata.decode())['data']
    except Exception as e:
        logger.error(NO_RESOURCE_FOUND.format(compareid))
        return None
    return resource




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
    resource = Documentcompare.query.filter(Documentcompare.compare_id == compareid).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(compareid))
    return resource

def get_doc_resource_by_id(id):
    g.aidocid = id
    resource = DocumentProcess.query.filter(DocumentProcess.id.like(str(id))).first()

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
            logger.error("Error while updating attribute to PD_document_attributes to DB for ID: {},{}".format(
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