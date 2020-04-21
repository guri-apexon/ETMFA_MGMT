import datetime
import logging
import os
from pathlib import Path
from datetime import datetime

from filehash import FileHash
from flask import g

from etmfa.consts import Consts as consts
from etmfa.db.db import db_context
from etmfa.db.models.documentProcess import DocumentProcess
from etmfa.db.models.documentattributes import Documentattributes
from etmfa.db.models.documentduplicate import Documentduplicate
from etmfa.db.models.documentfeedback import Documentfeedback
from etmfa.db.models.metric import Metric
from etmfa.db.models.processing import Processing
from etmfa.messaging.models.processing_status import ProcessingStatus
from etmfa.error import ManagementException
from etmfa.error import ErrorCodes

logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"
NO_RESOURCE_FOUND = "No document resource was found in DB for ID: {}"
ERROR_PROCESSING_STATUS = "Error while updating processing status to etmfa_document_process to DB for ID: {},{}"


# Global DB ORM object
def init_db(app):
    """ Returns db context"""

    # register database instance
    db_context.init_app(app)

    # create schema
    with app.app_context():
        # Create schema if not already created
        db_context.create_all()


def create_processing_config(kwargs):
    config = Processing.query.one_or_none()
    if config is not None:
        # update
        for key in kwargs:
            setattr(config, key, kwargs[key])
    else:
        # create
        config = Processing(**kwargs)
        db_context.session.add(config)

    db_context.session.commit()
    return config.as_dict()


def get_processing_config():
    config = Processing.query.one_or_none()
    if config is None:
        return None

    return config.as_dict()


def get_root_dir():
    config = get_processing_config()
    if config is None:
        raise ValueError("Processing directory must be configured before files can be uploaded")

    if not Path(config['processing_dir']):
        Path(config['processing_dir']).mkdir(exist_ok=True, parents=True)

    return config['processing_dir']


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

            exception = ManagementException(id, ErrorCodes.ERROR_PROCESSING_STATUS, ex)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error(ERROR_PROCESSING_STATUS.format(id, ex))

    return False


def received_feedbackcomplete_event(id):
    if update_doc_processing_status(id, ProcessingStatus.FEEDBACK_COMPLETED):
        # log message for feedback received is updated to DB from users/reviewers
        logger.info("Feedback received for id is updated to DB: {}".format(id))


def received_finalizationcomplete_event(id, finalattributes, message_publisher):
    if update_doc_processing_status(id, ProcessingStatus.PROCESS_COMPLETED):

        resource = get_doc_resource_by_id(id)

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
        attributes.fileName = safe_unicode(resource.fileName)
        attributes.documentFilePath = resource.documentFilePath
        attributes.customer = safe_unicode(finalattributes['customer'])
        attributes.protocol = safe_unicode(finalattributes['protocol'])
        attributes.country = safe_unicode(finalattributes['country'])
        attributes.site = safe_unicode(finalattributes['site'])
        attributes.docClass = finalattributes['doc_class']
        attributes.priority = finalattributes['priority']
        attributes.receivedDate = finalattributes['received_date']
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
            exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_ATTRIBUTES, ex)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error("Error while writing record to etmfa_document_attributes file in DB for ID: {},{}".format(
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
            logger.exception(f"Error while storing error message to etmfa_document_process DB table for ID: {error_dict['id']}")
    else:
        logger.error(NO_RESOURCE_FOUND.format(id))


def save_doc_feedback(_id, feedbackdata):
    recordfound = get_doc_resource_by_id(_id)

    resourcefb = Documentfeedback()

    resourcefb.p_id = str(int((datetime.now().timestamp()) * 1000000))
    resourcefb.id = feedbackdata['id']
    resourcefb.fileName = safe_unicode(recordfound.fileName)
    resourcefb.documentFilePath = recordfound.documentFilePath
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
        exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_FEEDBACK, ex)
        received_documentprocessing_error_event(exception.__dict__)
        logger.error("Error while writing record to etmfa_document_feedback file in DB for ID: {},{}".format(_id, ex))

    return resourcefb.as_dict()


def save_doc_processing_duplicate(request, _id, file_name, doc_path):
    resource = Documentduplicate()

    sha512hasher = FileHash('sha512')
    resource.id = _id
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
            exception = ManagementException(_id, ErrorCodes.ERROR_DOCUMENT_DUPLICATE, ex)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error(
                "Error while writing record to etmfa_document_duplicate file in DB for ID: {},{}".format(_id, ex))

    else:
        duplicateresource = resourcefound.id
        logger.info("Duplicate document id for the resource uploaded is: {}".format(duplicateresource))
        doc_duplicate_flag_update = resourcefound.docDuplicateFlag + 1
        last_updated = datetime.utcnow()
        setattr(resourcefound, 'docDuplicateFlag', doc_duplicate_flag_update)
        setattr(resourcefound, 'lastUpdated', last_updated)

        try:
            db_context.session.commit()
        except Exception as ex:
            db_context.session.rollback()
            exception = ManagementException(_id, ErrorCodes.ERROR_UPDATING_ATTRIBUTES, ex)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error(
                "Error while writing record to etmfa_document_duplicate file in DB for ID: {},{}".format(_id, ex))

    return duplicateresource


def get_doc_duplicate_by_id(resourcechk, full_mapping=False):
    if resourcechk.documentClass.lower() == 'core':
        resource = Documentduplicate.query.filter(Documentduplicate.docHash == resourcechk.docHash,
                                                  Documentduplicate.customer == resourcechk.customer,
                                                  Documentduplicate.protocol == resourcechk.protocol,
                                                  Documentduplicate.documentClass == resourcechk.documentClass.lower(),
                                                  Documentduplicate.country == None,
                                                  Documentduplicate.site == None,
                                                  Documentduplicate.documentRejected == False).first()
    elif resourcechk.documentClass.lower() == 'country':
        resource = Documentduplicate.query.filter(Documentduplicate.docHash == resourcechk.docHash,
                                                  Documentduplicate.customer == resourcechk.customer,
                                                  Documentduplicate.protocol == resourcechk.protocol,
                                                  Documentduplicate.documentClass == resourcechk.documentClass.lower(),
                                                  Documentduplicate.country == resourcechk.country,
                                                  Documentduplicate.site == None,
                                                  Documentduplicate.documentRejected == False).first()
    elif resourcechk.documentClass.lower() == 'site':
        resource = Documentduplicate.query.filter(Documentduplicate.docHash == resourcechk.docHash,
                                                  Documentduplicate.customer == resourcechk.customer,
                                                  Documentduplicate.protocol == resourcechk.protocol,
                                                  Documentduplicate.documentClass == resourcechk.documentClass.lower(),
                                                  Documentduplicate.country == resourcechk.country,
                                                  Documentduplicate.site == resourcechk.site,
                                                  Documentduplicate.documentRejected == False).first()
    else:
        resource = None

    return resource


def save_doc_processing(request, _id, doc_path):
    resource = DocumentProcess.from_post_request(request, _id, doc_path)

    resource.documentFilePath = doc_path

    resource.percentComplete = ProcessingStatus.TRIAGE_STARTED.value
    resource.status = ProcessingStatus.TRIAGE_STARTED.name

    try:
        db_context.session.add(resource)
        db_context.session.commit()
    except Exception as ex:
        print('hi')
        db_context.session.rollback()
        exception = ManagementException(id, ErrorCodes.ERROR_DOCUMENT_SAVING, ex)
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


def get_doc_attributes_by_id(id):
    g.aidocid = id
    resource = Documentattributes.query.filter(Documentattributes.id.like(str(id))).first()

    if resource is None:
        logger.error(NO_RESOURCE_FOUND.format(id))

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
            exception = ManagementException(id, ErrorCodes.ERROR_UPDATING_ATTRIBUTES, ex)
            received_documentprocessing_error_event(exception.__dict__)
            logger.error("Error while updating attribute to etmfa_document_attributes to DB for ID: {},{}".format(
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
