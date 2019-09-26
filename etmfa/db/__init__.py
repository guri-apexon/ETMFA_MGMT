import os, logging, time, json, requests
import pandas as pd
from filehash import FileHash

from datetime import datetime
from flask_migrate import Migrate
from lxml import html

# Global DB context must be initialized before local imports
from .db import db_context

from ..consts import Consts as consts
logger = logging.getLogger(consts.LOGGING_NAME)

from .models.processing import Processing
from .models.documentProcess import DocumentProcess
from .models.documentattributes import Documentattributes
from .models.documentfeedback import Documentfeedback
from .models.metric import Metric
from .models.documentduplicate import Documentduplicate
from ..messaging.models.ocr_request import ocrrequest
from ..messaging.models.classification_request import classificationRequest
from ..messaging.models.attributeextraction_request import attributeextractionRequest
from ..messaging.models.finalization_request import finalizationRequest
#os.environ["NLS_LANG"] = "RUSSIAN_RUSSIA.AL32UTF8"
#os.environ["NLS_LANG"] = "AMERICAN_AMERICA.CL8MSWIN1251"
os.environ["NLS_LANG"]="AMERICAN_AMERICA.AL32UTF8"

from . import *

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
    if config != None:
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
    if config == None:
        return None

    return config.as_dict()

def get_root_dir():
    config = get_processing_config()
    if config == None:
        raise ValueError("Processing directory must be configured before files can be uploaded")

    if not os.path.exists(config['processing_dir']):
        os.makedirs(config['processing_dir'])

    return config['processing_dir']


def received_triagecomplete_event(id, IQVXMLPath, message_publisher):
    resource = get_doc_resource_by_id(id)

    if resource is not None:
        resource.percentComplete = '30'
        resource.status = "OCR_STARTED"
        resource.lastUpdated = datetime.utcnow()
        try:
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))
            raise LookupError("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))

        # Start processing OCR request
        OCR_req_msg = ocrrequest(id, IQVXMLPath)
        message_publisher.send_obj(OCR_req_msg)

    else:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))


def received_ocrcomplete_event(id, IQVXMLPath, message_publisher):
    resource = get_doc_resource_by_id(id)

    if resource is not None:
        resource.percentComplete = '70'
        resource.status = "CLASSIFICATION_STARTED"
        resource.lastUpdated = datetime.utcnow()
        try:
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))
            raise LookupError("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))

        # Start processing Classification request
        classification_req_msg = classificationRequest(id, IQVXMLPath)
        message_publisher.send_obj(classification_req_msg)
    else:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))


def received_classificationcomplete_event(id, IQVXMLPath, message_publisher):
    resource = get_doc_resource_by_id(id)

    if resource is not None:
        resource.percentComplete = '80'
        resource.status = "ATTRIBUTEEXTRACTION_STARTED"
        resource.lastUpdated = datetime.utcnow()
        try:
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))
            raise LookupError("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))

        # Start processing Extraction request
        attributeextraction_req_msg = attributeextractionRequest(id,IQVXMLPath)
        message_publisher.send_obj(attributeextraction_req_msg)
    else:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))


def received_attributeextractioncomplete_event(id, IQVXMLPath, message_publisher):
    resource = get_doc_resource_by_id(id)

    if resource is not None:
        resource.percentComplete = '90'
        resource.status = "FINALIZATION_STARTED"
        resource.lastUpdated = datetime.utcnow()
        try:
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))
            raise LookupError("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))

        # Start processing finalizer request
        finalization_req_msg = finalizationRequest(id,IQVXMLPath)
        message_publisher.send_obj(finalization_req_msg)
    else:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))

def received_feedbackcomplete_event(id):
    resource = get_doc_resource_by_id(id)

    if resource is not None:
        resource.percentComplete = '100'
        resource.status = "FEEDBACK_COMPLETED"
        resource.lastUpdated = datetime.utcnow()
        try:
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))
            raise LookupError("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))
    else:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))

def received_finalizationcomplete_event(id, finalattributes, message_publisher):
    resource = get_doc_resource_by_id(id)

    if resource is not None:
        resource.isProcessing = False
        resource.percentComplete = '100'
        resource.status = "PROCESS_COMPLETED"
        resource.lastUpdated = datetime.utcnow()
        try:
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))
            raise LookupError("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(id, e))

        metrics = Metric(resource.id)
        metrics.id                             = finalattributes['id']
        metrics.totalProcessTime               = finalattributes['total_process_time']
        metrics.queueWaitTime                  = finalattributes['queue_wait_time']
        metrics.triageMachineName              = finalattributes['triage_machine_name']
        metrics.triageVersion                  = finalattributes['triage_version']
        metrics.triageStartTime                = finalattributes['triage_start_time']
        metrics.triageEndTime                  = finalattributes['triage_end_time']
        metrics.triageProcTime                 = finalattributes['triage_proc_time']
        metrics.digitizerMachineName           = finalattributes['digitizer_machine_name']
        metrics.digitizerVersion               = finalattributes['digitizer_version']
        metrics.digitizerStartTime             = finalattributes['digitizer_start_time']
        metrics.digitizerEndTime               = finalattributes['digitizer_end_time']
        metrics.digitizerProcTime              = finalattributes['digitizer_proc_time']
        metrics.classificationMachineName      = finalattributes['classification_machine_name']
        metrics.classificationVersion          = finalattributes['classification_version']
        metrics.classificationStartTime        = finalattributes['classification_start_time']
        metrics.classificationEndTime          = finalattributes['classification_end_time']
        metrics.classificationProcTime         = finalattributes['classification_proc_time']
        metrics.attExtractionMachineName       = finalattributes['att_extraction_machine_name']
        metrics.attExtractionVersion           = finalattributes['att_extraction_version']
        metrics.attExtractionStartTime         = finalattributes['att_extraction_start_time']
        metrics.attExtractionEndTime           = finalattributes['att_extraction_end_time']
        metrics.attExtractionProcTime          = finalattributes['att_extraction_proc_time']
        metrics.finalizationMachineName        = finalattributes['finalization_machine_name']
        metrics.finalizationVersion            = finalattributes['finalization_version']
        metrics.finalizationStartTime          = finalattributes['finalization_start_time']
        metrics.finalizationEndTime            = finalattributes['finalization_end_time']
        metrics.finalizationProcTime           = finalattributes['finalization_proc_time']
        metrics.docType                        = finalattributes['doc_type']
        metrics.docTypeOriginal                = finalattributes['doc_type_original']
        metrics.docSegments                    = finalattributes['doc_segments']
        metrics.docPages                       = finalattributes['doc_pages']


        attributes                             = Documentattributes()
        attributes.id                          = finalattributes['id']
        attributes.fileName                    = safe_unicode(resource.fileName)
        attributes.documentFilePath            = resource.documentFilePath
        attributes.customer                    = safe_unicode(finalattributes['customer'])
        attributes.protocol                    = safe_unicode(finalattributes['protocol'])
        attributes.country                     = safe_unicode(finalattributes['country'])
        attributes.site                        = safe_unicode(finalattributes['site'])
        attributes.docClass                    = finalattributes['doc_class']
        attributes.priority                    = finalattributes['priority']
        attributes.receivedDate                = finalattributes['received_date']
        attributes.sitePersonnelList           = safe_unicode(finalattributes['site_personnel_list'])
        attributes.tmfEnvironment              = finalattributes['tmf_environment']
        attributes.tmfIbr                      = finalattributes['tmf_ibr']

        attributes.docCompConf                 = finalattributes['doc_comp_conf']
        attributes.docClassification           = finalattributes['doc_classification']
        attributes.docClassificationConf       = finalattributes['doc_classification_conf']
        attributes.docDate                     = finalattributes['doc_date']
        attributes.docDateConf                 = finalattributes['doc_date_conf']
        attributes.docDateType                 = finalattributes['doc_date_type']
        attributes.name                        = safe_unicode(finalattributes['name'])
        attributes.nameConf                    = finalattributes['name_conf']
        attributes.language                    = finalattributes['language']
        attributes.languageConf                = finalattributes['language_conf']
        attributes.subject                     = safe_unicode(finalattributes['subject'])
        attributes.subjectConf                 = finalattributes['subject_conf']
        attributes.alcoacCheckError            = finalattributes['alcoac_check_error']
        attributes.alcoacCheckCompScore        = finalattributes['alcoac_check_comp_score']
        attributes.alcoacCheckCompScoreConf    = finalattributes['alcoac_check_comp_score_conf']
        attributes.docSubclassification        = finalattributes['doc_subclassification']
        attributes.docSubclassificationConf    = finalattributes['doc_subclassification_conf']
        attributes.docClassificationElvis      = finalattributes['doc_classification_elvis']

        if finalattributes['blinded'] in ['true', 'yes', 'True', 'TRUE', 'YES', 'Yes', 'y', 'Y']:
            attributes.unblinded = True
        else:
            attributes.blinded = False

        try:
            db_context.session.add(attributes)
            db_context.session.add(metrics)
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while writing record to etmfa_document_attributes file in DB for ID: {},{}".format(finalattributes['id'],e))
            raise LookupError("Error while writing record to etmfa_document_attributes file in DB for ID: {},{}".format(finalattributes['id'],e))
    else:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))

def received_documentprocessing_error_event(errorDict):
    resource = get_doc_resource_by_id(errorDict['id'])

    if resource is not None:
        # Update error status for the document
        resource.errorCode = errorDict['error_code']
        resource.errorReason = errorDict['service_name'] + errorDict['error_message']
        resource.status = "ERROR"

        resource.isProcessing = False
        resource.lastUpdated = datetime.utcnow()

        try:
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while updating values to etmfa_document_process file in DB for ID: {},{}".format(errorDict['id'],e))
            raise LookupError("Error while updating values to etmfa_document_process file in DB for ID: {},{}".format(errorDict['id'],e))
    else:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))


def save_doc_feedback(_id, feedbackdata):

    recordfound = get_doc_resource_by_id(_id)

    resourcefb = Documentfeedback()

    resourcefb.p_id                     = str(int((datetime.now().timestamp()) * 1000000))
    resourcefb.id                       = feedbackdata['id']
    resourcefb.fileName                 = safe_unicode(recordfound.fileName)
    resourcefb.documentFilePath         = recordfound.documentFilePath
    resourcefb.feedbackSource           = feedbackdata['feedbackSource']
    resourcefb.customer                 = safe_unicode(feedbackdata['customer'])
    resourcefb.protocol                 = safe_unicode(feedbackdata['protocol'])
    resourcefb.country                  = safe_unicode(feedbackdata['country'])
    resourcefb.site                     = safe_unicode(feedbackdata['site'])
    resourcefb.documentClass            = feedbackdata['documentClass']
    resourcefb.documentDate             = feedbackdata['documentDate']
    resourcefb.documentClassification   = feedbackdata['documentClassification']
    resourcefb.name                     = safe_unicode(feedbackdata['name'])
    resourcefb.language                 = feedbackdata['language']
    resourcefb.documentRejected         = feedbackdata['documentRejected']
    resourcefb.attributeAuxillaryList   = safe_unicode(str(feedbackdata['attributeAuxillaryList']))

    try:
        db_context.session.add(resourcefb)
        db_context.session.commit()
    except Exception as e:
        db_context.session.rollback()
        #db_context.session.remove()
        logger.error("Error while writing record to etmfa_document_feedback file in DB for ID: {},{}".format(_id, e))
        raise LookupError("Error while writing record to etmfa_document_feedback file in DB for ID: {},{}".format(_id, e))

    return resourcefb.as_dict()

def save_doc_processing_duplicate(request, _id, fileName, doc_path):
    resource = Documentduplicate()

    sha512hasher = FileHash('sha512')
    resource.id                  = _id
    resource.fileName            = safe_unicode(fileName)
    resource.docHash             = sha512hasher.hash_file(doc_path)
    resource.documentFilePath    = doc_path
    resource.customer            = safe_unicode(request['customer']) if request['customer'] is not None else ''
    resource.protocol            = safe_unicode(request['protocol']) if request['protocol'] is not None else ''
    resource.country             = safe_unicode(request['country'])  if request['country'] is not None else ''
    resource.site                = safe_unicode(request['site']) if request['site'] is not None else ''
    resource.documentClass       = request['documentClass'] if request['documentClass'] is not None else ''
    resource.receivedDate        = request['receivedDate']  if request['receivedDate'] is not None else ''

    resourcefound = get_doc_duplicate_by_id(resource)
    duplicateresource = ' '

    if resourcefound is None:
        resource.docDuplicateFlag = 0
        try:
            db_context.session.add(resource)
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while writing record to etmfa_document_duplicate file in DB for ID: {},{}".format(_id, e))
            raise LookupError("Error while writing record to etmfa_document_duplicate file in DB for ID: {},{}".format(_id, e))
    else:
        duplicateresource = resourcefound.id
        doc_duplicate_flag_update  = resourcefound.docDuplicateFlag + 1
        setattr(resourcefound, 'docDuplicateFlag', doc_duplicate_flag_update)
        try:
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while writing record to etmfa_document_duplicate file in DB for ID: {},{}".format(_id, e))
            raise LookupError("Error while writing record to etmfa_document_duplicate file in DB for ID: {},{}".format(_id, e))

    return duplicateresource

def get_doc_duplicate_by_id(resourcechk, full_mapping=False):

    if resourcechk.documentClass == 'core':
        resource = Documentduplicate.query.filter(Documentduplicate.docHash  == resourcechk.docHash and
                                                  Documentduplicate.customer == resourcechk.customer and
                                                  Documentduplicate.protocol == resourcechk.protocol and
                                                  Documentduplicate.documentRejected == False).first()
    elif resourcechk.documentClass == 'country':
        resource = Documentduplicate.query.filter(Documentduplicate.docHash  == resourcechk.docHash and
                                                  Documentduplicate.customer == resourcechk.customer and
                                                  Documentduplicate.protocol == resourcechk.protocol and
                                                  Documentduplicate.country  == resourcechk.country and
                                                  Documentduplicate.documentRejected == False).first()
    elif resourcechk.documentClass == 'site':
        resource = Documentduplicate.query.filter(Documentduplicate.docHash == resourcechk.docHash and
                                                  Documentduplicate.customer == resourcechk.customer and
                                                  Documentduplicate.protocol == resourcechk.protocol and
                                                  Documentduplicate.country  == resourcechk.country and
                                                  Documentduplicate.site     == resourcechk.site and
                                                  Documentduplicate.documentRejected == False).first()
    else:
        resource = Documentduplicate.query.filter(Documentduplicate.docHash == resourcechk.docHash).first()

    if not full_mapping:
        return resource

    return resource

def save_doc_processing(request, _id, doc_path):
    resource = DocumentProcess.from_post_request(request, _id, doc_path)

    resource.documentFilePath = doc_path
    resource.percentComplete = '0'
    resource.status = "TRIAGE_STARTED"
    try:
        db_context.session.add(resource)
        db_context.session.commit()
    except Exception as e:
        db_context.session.rollback()
        logger.error("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(_id, e))
        raise LookupError("Error while updating processing status to etmfa_document_process to DB for ID: {},{}".format(_id, e))


def get_doc_processing_by_id(id, full_mapping=False):
    resource_dict = get_doc_resource_by_id(id).as_dict()

    if not full_mapping:
        return resource_dict

    return resource_dict

def get_doc_processed_by_id(id, full_mapping=True):
    resource_dict = get_doc_attributes_by_id(id)

    if not full_mapping:
        return resource_dict

    return resource_dict

def get_doc_proc_metrics_by_id(id, full_mapping=True):
    resource_dict = get_doc_metrics_by_id(id)

    if not full_mapping:
        return resource_dict

    return resource_dict

def get_doc_attributes_by_id(id):
    resource = Documentattributes.query.filter(Documentattributes.id.like(str(id))).first()

    if resource == None:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        #raise LookupError("No document resource was found in DB for ID: {}".format(id))

    return resource

def get_doc_metrics_by_id(id):
    resource = Metric.query.filter(Metric.id.like(str(id))).first()

    if resource == None:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        #raise LookupError("No document resource was found in DB for ID: {}".format(id))

    return resource

def get_doc_status_processing_by_id(id, full_mapping=True):
    resource_dict = get_doc_resource_by_id(id)

    if not full_mapping:
        return resource_dict

    return resource_dict


def get_doc_resource_by_id(id):
    resource = DocumentProcess.query.filter(DocumentProcess.id.like(str(id))).first()

    if resource == None:
        logger.error("No document resource was found in DB for ID: {}".format(id))

    return resource


def upsert_attributevalue(doc_processing_id, namekey, value):
    doc_processing_resource = get_doc_attributes_by_id(doc_processing_id)

    if doc_processing_resource is None:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))
    else:
        try:
            setattr(doc_processing_resource, namekey, value)
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            logger.error("Error while updating attribute to etmfa_document_attributes to DB for ID: {},{}".format(doc_processing_id, e))
            raise LookupError("Error while updating attribute to etmfa_document_attributes to DB for ID: {},{}".format(doc_processing_id, e))


def get_attribute_dict(doc_processing_id):
    doc_processing_resource = get_doc_resource_by_id(doc_processing_id)

    if doc_processing_resource == None:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))

    return doc_processing_resource

def safe_unicode(obj, *args):
    """ return the unicode representation of obj """
    try:
        return str(obj, *args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return str(ascii_text)
