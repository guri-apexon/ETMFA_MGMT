import os, logging, time, json, requests
import pandas as pd

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
#from .status import StatusEnum
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
    except:
        db_context.session.rollback()
        raise LookupError("Error while writing record to etmfa_document_metrics to DB for ID: {}".format(finalattributes['id']))


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
    attributes.alcoal_check_error          = finalattributes['alcoac_check_error']
    attributes.doc_rejected                = ' '
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
    except:
        db_context.session.rollback()
        raise LookupError("Error while writing record to etmfa_document_attributes file in DB for ID: {}".format(finalattributes['id']))

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

    resource = Documentfeedback()

    resource.p_id                     = str(int((datetime.now().timestamp()) * 1000000))
    resource.id                       = feedbackdata['id']
    resource.document_file_path       = recordfound.document_file_path
    resource.feedback_source          = feedbackdata['feedback_source']
    resource.customer                 = feedbackdata['customer']
    resource.protocol                 = feedbackdata['protocol']
    resource.country                  = feedbackdata['country']
    resource.site                     = feedbackdata['site']
    resource.document_class           = feedbackdata['document_class']
    resource.document_date            = feedbackdata['document_date']
    resource.document_classification  = feedbackdata['document_classification']
    resource.name                     = feedbackdata['name']
    resource.language                 = feedbackdata['language']
    resource.document_rejected        = feedbackdata['document_rejected']
    resource.attribute_auxillary_list = str(feedbackdata['attribute_auxillary_list'])


    db_context.session.add(resource)
    try:
        db_context.session.commit()
    except:
        db_context.session.rollback()
        raise LookupError("Error while writing record to etmfa_document_feedback file in DB for ID: {}".format(_id))

    return resource.as_dict()


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

# def upsert_processing_metric(doc_processing_id, property_name, val):
#     """Adds or updates a name-value pair of a metric, referenced by a processing resource.
#
#     Args:
#         doc_processing_id (int): Doc processing resource id
#         property_name (str): Metric field name
#         val (int): Metric value
#     """
#     doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
#     metric = Metric.query.filter(Metric.document_processing_id==doc_processing_resource.p_id).first()
#
#     if metric == None:
#         metric = Metric(doc_processing_resource.p_id)
#
#     processing_metric = processingMetric(metric.id, property_name, val)
#     formatting_metric = FormattingMetric(metric.id, 'test', 'test')
#     metric.processing_metrics.append(processing_metric)
#
#     db_context.session.add(metric)
#     db_context.session.commit()

# def get_metrics_dict(doc_processing_id):
#     doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
#     metric = Metric.query.filter(Metric.document_processing_id == doc_processing_resource.p_id).first()
#     m_dict = {'DocumentProcessing_metrics': []}
#
#     if metric == None:
#         return m_dict
#
#     if metric.documentprocessing_metrics != None:
#         m_dict['DocumentProcessing_metrics'] = [{'name': m.name, 'val': m.value} for m in metric.documentprocessing_metrics]
#
#     return m_dict

# def upsert_metadata(doc_processing_id, name, value):
#     doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
#
#     # Make sure name doesn't already exist
#     metadata = IQMetadata.query.filter(IQMetadata.name==name).first()
#     if not metadata:
#         # Create
#         metadata = IQMetadata(doc_processing_id, name, value)
#         doc_processing_resource.iq_metadata.append(metadata)
#     else:
#         # Update
#         metadata.value = value
#
#     db_context.session.add(doc_processing_resource)
#     db_context.session.commit()

def upsert_attributevalue(doc_processing_id, namekey, value):
    doc_processing_resource = get_doc_attributes_by_id(doc_processing_id)

    if doc_processing_resource is None:
        raise LookupError("No resource was found in DB for ID: {}".format(id))
    else:
        setattr(doc_processing_resource, namekey, value)
        db_context.session.commit()

# def get_attributevalue(doc_processing_id, keydict):
#         doc_processing_resource = get_doc_attributes_by_id(doc_processing_id)
#
#         m_dict = {'metadata': []}
#         if doc_processing_resource is None:
#             raise LookupError("No resource was found in DB for ID: {}".format(id))
#             return m_dict
#         else:
#             for m in keydict:
#                 m_dict['metadata'].append({'name': m.name, 'val': getattr(doc_processing_resource,m.name)})
#
#             return m_dict

def get_attribute_dict(doc_processing_id):
    doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
    #metadata = IQMetadata.query.filter(IQMetadata.document_processing_id==doc_processing_resource.p_id)

    if doc_processing_resource == None:
        raise LookupError("No resource was found in DB for ID: {}".format(id))

    return doc_processing_resource


# def get_metadata_dict(doc_processing_id):
#     doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
#     metadata = IQMetadata.query.filter(IQMetadata.document_processing_id==doc_processing_resource.p_id)
#
#     m_dict = {'metadata': []}
#     if metadata == None:
#         return m_dict
#
#     for m in metadata:
#         m_dict['metadata'].append({'name': m.name, 'val': m.value})
#
#     return m_dict

