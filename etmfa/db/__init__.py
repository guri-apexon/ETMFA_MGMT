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

    resource.Percent_complete = '30'
    resource.status = "OCR_STARTED"
    resource.last_updated = datetime.utcnow()
    db_context.session.commit()

    # Start processing request
    OCR_req_msg = ocrrequest(
        id,
        IQVXMLPath
    )

    message_publisher.send_obj(OCR_req_msg)

    return resource.as_dict()

def received_ocrcomplete_event(id, IQVXMLPath, message_publisher):
    resource = get_doc_resource_by_id(id)

    resource.Percent_complete = '70'
    resource.status = "CLASSIFICATION_STARTED"
    resource.last_updated = datetime.utcnow()
    db_context.session.commit()

    # Start processing request
    classification_req_msg = classificationRequest(
        id,
        IQVXMLPath
    )

    message_publisher.send_obj(classification_req_msg)

    return resource.as_dict()

def received_classificationcomplete_event(id, IQVXMLPath, message_publisher):
    resource = get_doc_resource_by_id(id)

    resource.Percent_complete = '80'
    resource.status = "ATTRIBUTEEXTRACTION_STARTED"
    resource.last_updated = datetime.utcnow()
    db_context.session.commit()

    # Start processing request
    attributeextraction_req_msg = attributeextractionRequest(
        id,
        IQVXMLPath
    )

    message_publisher.send_obj(attributeextraction_req_msg)

    return resource.as_dict()

def received_attributeextractioncomplete_event(id, IQVXMLPath, message_publisher):
    resource = get_doc_resource_by_id(id)

    resource.Percent_complete = '90'
    resource.status = "FINALIZATION_STARTED"
    resource.last_updated = datetime.utcnow()
    db_context.session.commit()

    # Start processing request
    finalization_req_msg = finalizationRequest(
        id,
        IQVXMLPath
    )

    message_publisher.send_obj(finalization_req_msg)

    return resource.as_dict()

def received_feedbackcomplete_event(id):
    resource = get_doc_resource_by_id(id)
    resource.Percent_complete = '100'
    resource.status = "FEEDBACK_COMPLETED"
    resource.last_updated = datetime.utcnow()

    db_context.session.commit()

    return resource.as_dict()


def received_finalizationcomplete_event(id, finalattributes, message_publisher):
    resource = get_doc_resource_by_id(id)

    resource.is_processing = False
    resource.Percent_complete = '100'
    resource.status = "PROCESS_COMPLETED"
    resource.last_updated = datetime.utcnow()
    db_context.session.commit()

    metrics = Metric(resource.id)
    metrics.id                             = finalattributes['id']
    metrics.total_process_time             = finalattributes['total_process_time']
    metrics.queue_wait_time                = finalattributes['queue_wait_time']
    metrics.triage_machine_name            = finalattributes['triage_machine_name']
    metrics.triage_version                 = finalattributes['triage_version']
    metrics.triage_start_time              = finalattributes['triage_start_time']
    metrics.triage_end_time                = finalattributes['triage_end_time']
    metrics.triage_proc_time               = finalattributes['triage_proc_time']
    metrics.digitizer_machine_name         = finalattributes['digitizer_machine_name']
    metrics.digitizer_version              = finalattributes['digitizer_version']
    metrics.digitizer_start_time           = finalattributes['digitizer_start_time']
    metrics.digitizer_end_time             = finalattributes['digitizer_end_time']
    metrics.digitizer_proc_time            = finalattributes['digitizer_proc_time']
    metrics.classification_machine_name    = finalattributes['classification_machine_name']
    metrics.classification_version         = finalattributes['classification_version']
    metrics.classification_start_time      = finalattributes['classification_start_time']
    metrics.classification_end_time        = finalattributes['classification_end_time']
    metrics.classification_proc_time       = finalattributes['classification_proc_time']
    metrics.att_extraction_machine_name    = finalattributes['att_extraction_machine_name']
    metrics.att_extraction_version         = finalattributes['att_extraction_version']
    metrics.att_extraction_start_time      = finalattributes['att_extraction_start_time']
    metrics.att_extraction_end_time        = finalattributes['att_extraction_end_time']
    metrics.att_extraction_proc_time       = finalattributes['att_extraction_proc_time']
    metrics.finalization_machine_name      = finalattributes['finalization_machine_name']
    metrics.finalization_version           = finalattributes['finalization_version']
    metrics.finalization_start_time        = finalattributes['finalization_start_time']
    metrics.finalization_end_time          = finalattributes['finalization_end_time']
    metrics.finalization_proc_time         = finalattributes['finalization_proc_time']

    db_context.session.add(metrics)
    try:
        db_context.session.commit()
    except Exception as e:
        db_context.session.rollback()
        raise LookupError("Error while writing record to etmfa_document_metrics to DB for ID: {},{}".format(finalattributes['id'], e))


    attributes                             = Documentattributes()
    attributes.id                          = finalattributes['id']
    attributes.doc_comp_conf               = finalattributes['doc_comp_conf']
    attributes.customer                    = finalattributes['customer']
    attributes.protocol                    = finalattributes['protocol']
    attributes.country                     = finalattributes['country']
    attributes.site                        = finalattributes['site']
    attributes.doc_class                   = finalattributes['doc_class']
    attributes.doc_date                    = finalattributes['doc_date']
    attributes.doc_date_conf               = finalattributes['doc_date_conf']
    attributes.doc_date_type               = finalattributes['doc_date_type']
    attributes.doc_classification          = finalattributes['doc_classification']
    attributes.doc_classification_conf     = finalattributes['doc_classification_conf']
    attributes.name                        = finalattributes['name']
    attributes.name_conf                   = finalattributes['name_conf']
    attributes.doc_subclassification       = finalattributes['doc_subclassification']
    attributes.doc_subclassification_conf  = finalattributes['doc_subclassification_conf']
    attributes.subject                     = finalattributes['subject']
    attributes.subject_conf                = finalattributes['subject_conf']
    attributes.language                    = finalattributes['language']
    attributes.language_conf               = finalattributes['language_conf']
    attributes.alcoac_check_comp_score     = finalattributes['alcoac_check_comp_score']
    attributes.alcoac_check_comp_score_conf= finalattributes['alcoac_check_comp_score_conf']
    attributes.alcoac_check_error          = finalattributes['alcoac_check_error']
    #attributes.doc_rejected                = ' '
    attributes.priority                    = finalattributes['priority']
    attributes.received_date               = finalattributes['received_date']
    attributes.site_personnel_list         = finalattributes['site_personnel_list']
    attributes.tmf_environment             = finalattributes['tmf_environment']
    attributes.tmf_ibr                     = finalattributes['tmf_ibr']
    attributes.doc_classification_elvis    = finalattributes['doc_classification_elvis']
    if finalattributes['blinded'] in ['true', 'yes', 'True', 'TRUE', 'YES', 'Yes', 'y', 'Y']:
        attributes.blinded = True
    else:
        attributes.blinded = False


    db_context.session.add(attributes)
    try:
        db_context.session.commit()
    except Exception as e:
        db_context.session.rollback()
        raise LookupError("Error while writing record to etmfa_document_attributes file in DB for ID: {},{}".format(finalattributes['id'],e))

    return resource.as_dict()


def received_documentprocessing_error_event(errorDict):
    resource = get_doc_resource_by_id(errorDict['id'])

    # Update status
    resource.error_code = errorDict['error_code']
    resource.error_reason = errorDict['service_name'] + errorDict['error_message']
    resource.status = "ERROR"

    resource.is_processing = False
    resource.last_updated = datetime.utcnow()

    db_context.session.commit()


def save_doc_feedback(_id, feedbackdata):

    recordfound = get_doc_resource_by_id(_id)

    resourcefb = Documentfeedback()

    resourcefb.p_id                     = str(int((datetime.now().timestamp()) * 1000000))
    resourcefb.id                       = feedbackdata['id']
    resourcefb.document_file_path       = recordfound.document_file_path
    resourcefb.feedback_source          = feedbackdata['feedback_source']
    resourcefb.customer                 = feedbackdata['customer']
    resourcefb.protocol                 = feedbackdata['protocol']
    resourcefb.country                  = feedbackdata['country']
    resourcefb.site                     = feedbackdata['site']
    resourcefb.document_class           = feedbackdata['document_class']
    resourcefb.document_date            = feedbackdata['document_date']
    resourcefb.document_classification  = feedbackdata['document_classification']
    resourcefb.name                     = feedbackdata['name']
    resourcefb.language                 = feedbackdata['language']
    resourcefb.document_rejected        = feedbackdata['document_rejected']
    resourcefb.attribute_auxillary_list = str(feedbackdata['attribute_auxillary_list'])

    db_context.session.add(resourcefb)
    try:
        db_context.session.commit()
    except Exception as e:
        db_context.session.rollback()
        raise LookupError("Error while writing record to etmfa_document_feedback file in DB for ID: {},{}".format(_id, e))

    return resourcefb.as_dict()

def save_doc_processing_duplicate(request, _id, doc_path):
    resource = Documentduplicate()

    sha512hasher = FileHash('sha512')
    resource.id                  = _id
    resource.doc_hash            = sha512hasher.hash_file(doc_path)
    resource.document_file_path  = doc_path
    resource.customer            = request['Customer'] if request['Customer'] is not None else ''
    resource.protocol            = request['Protocol'] if request['Protocol'] is not None else ''
    resource.country             = request['Country']  if request['Country'] is not None else ''
    resource.site                = request['Site']     if request['Site'] is not None else ''
    resource.document_class      = request['Document_Class'] if request['Document_Class'] is not None else ''
    resource.received_date       = request['Received_Date']  if request['Received_Date'] is not None else ''
    #resource.document_rejected   = request['Document_Rejected']
    resourcefound = get_doc_duplicate_by_id(resource)
    duplicateresource = ' '
    if resourcefound is None:
        resource.doc_duplicate_flag = 0
        try:
            db_context.session.add(resource)
            db_context.session.commit()
        except Exception as e:
            db_context.session.rollback()
            raise LookupError(
                "Error while writing record to etmfa_document_duplicate file in DB for ID: {},{}".format(_id, e))
    else:
        duplicateresource = resourcefound.id
        doc_duplicate_flag_update  = resourcefound.doc_duplicate_flag + 1
        setattr(resourcefound, 'doc_duplicate_flag', doc_duplicate_flag_update)
        db_context.session.commit()

    return duplicateresource

def get_doc_duplicate_by_id(resourcechk, full_mapping=False):

    if resourcechk.document_class == 'core':
        resource = Documentduplicate.query.filter(Documentduplicate.doc_hash == resourcechk.doc_hash and
                                                  Documentduplicate.customer == resourcechk.customer and
                                                  Documentduplicate.protocol == resourcechk.protocol and
                                                  Documentduplicate.document_rejected == False).first()
    elif resourcechk.document_class == 'country':
        resource = Documentduplicate.query.filter(Documentduplicate.doc_hash == resourcechk.doc_hash and
                                                  Documentduplicate.customer == resourcechk.customer and
                                                  Documentduplicate.protocol == resourcechk.protocol and
                                                  Documentduplicate.country  == resourcechk.country and
                                                  Documentduplicate.document_rejected == False).first()
    elif resourcechk.document_class == 'site':
        resource = Documentduplicate.query.filter(Documentduplicate.doc_hash == resourcechk.doc_hash and
                                                  Documentduplicate.customer == resourcechk.customer and
                                                  Documentduplicate.protocol == resourcechk.protocol and
                                                  Documentduplicate.country  == resourcechk.country and
                                                  Documentduplicate.site     == resourcechk.site and
                                                  Documentduplicate.document_rejected == False).first()
    else:
        resource = Documentduplicate.query.filter(Documentduplicate.doc_hash == resourcechk.doc_hash).first()

    if not full_mapping:
        return resource

    return resource

def save_doc_processing(request, _id, doc_path):
    resource = DocumentProcess.from_post_request(request, _id, doc_path)

    resource.document_file_path = doc_path
    resource.Percent_complete = '0'
    resource.status = "TRIAGE_STARTED"
    db_context.session.add(resource)
    db_context.session.commit()

    return resource.as_dict()


def get_doc_processing_by_id(id, full_mapping=False):
    resource_dict = get_doc_resource_by_id(id).as_dict()

    if not full_mapping:
        return resource_dict

    return resource_dict

def get_doc_processed_by_id(id, full_mapping=True):
    resource_dict = get_doc_attributes_by_id(id).as_dict()

    if not full_mapping:
        return resource_dict

    return resource_dict

def get_doc_proc_metrics_by_id(id, full_mapping=True):
    resource_dict = get_doc_metrics_by_id(id).as_dict()

    if not full_mapping:
        return resource_dict

    return resource_dict

def get_doc_attributes_by_id(id):
    """
    Returns the DTO by id.
    Raises LookupError if no id is found.
    """

    resource = Documentattributes.query.filter(Documentattributes.id.like(str(id))).first()

    if resource == None:
        raise LookupError("No resource was found in DB for ID: {}".format(id))

    return resource

def get_doc_metrics_by_id(id):
    """
    Returns the DTO by id.
    Raises LookupError if no id is found.
    """

    resource = Metric.query.filter(Metric.id.like(str(id))).first()

    if resource == None:
        raise LookupError("No resource was found in DB for ID: {}".format(id))

    return resource

def get_doc_status_processing_by_id(id, full_mapping=True):
    resource_dict = get_doc_resource_by_id(id).as_dict()

    if not full_mapping:
        return resource_dict

    return resource_dict


def get_doc_resource_by_id(id):
    """
    Returns the DTO by id.
    Raises LookupError if no id is found.
    """

    resource = DocumentProcess.query.filter(DocumentProcess.id.like(str(id))).first()

    if resource == None:
        logger.error("No document resource was found in DB for ID: {}".format(id))
        raise LookupError("No document resource was found in DB for ID: {}".format(id))

    return resource


def upsert_attributevalue(doc_processing_id, namekey, value):
    doc_processing_resource = get_doc_attributes_by_id(doc_processing_id)

    if doc_processing_resource is None:
        raise LookupError("No resource was found in DB for ID: {}".format(id))
    else:
        setattr(doc_processing_resource, namekey, value)
        db_context.session.commit()


def get_attribute_dict(doc_processing_id):
    doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
    #metadata = IQMetadata.query.filter(IQMetadata.document_processing_id==doc_processing_resource.p_id)

    if doc_processing_resource == None:
        raise LookupError("No resource was found in DB for ID: {}".format(id))

    return doc_processing_resource


