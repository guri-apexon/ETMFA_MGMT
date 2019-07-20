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
from .status import StatusEnum
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
    resource.status = StatusEnum.OCR_STARTED
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
    resource.status = StatusEnum.CLASSIFICATION_STARTED
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
    resource.status = StatusEnum.ATTRIBUTEEXTRACTION_STARTED
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
    resource.status = StatusEnum.FINALIZATION_STARTED
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
    # print("record received for processing feedback complete 1")
    #
    # resource.Percent_complete = '100'
    # resource.status = StatusEnum.FEEDBACK_COMPLETED
    # resource.last_updated = datetime.utcnow()
    # print("record received for processing feedback complete 2")
    #
    # db_context.session.commit()
    # print("record received for processing feedback complete 3")

    return resource.as_dict()


def received_finalizationcomplete_event(id, finalattributes, message_publisher):
    resource = get_doc_resource_by_id(id)

    resource.is_processing = False
    resource.Percent_complete = '100'
    resource.status = StatusEnum.PROCESS_COMPLETED
    resource.last_updated = datetime.utcnow()
    db_context.session.commit()

    metrics = Metric(resource.id)
    metrics.id                             = finalattributes['id']
    #metrics.document_processing_id         = finalattributes['id']
    metrics.triage_start_time              = finalattributes['triage_start_time']
    metrics.triage_end_time                = finalattributes['triage_end_time']
    metrics.triage_proc_time               = finalattributes['triage_process_time']
    metrics.digitizer_start_time           = finalattributes['digitizer_start_time']
    metrics.digitizer_end_time             = finalattributes['digitizer_end_time']
    metrics.digitizer_proc_time            = finalattributes['digitizer_process_time']
    metrics.classification_start_time      = finalattributes['classification_start_time']
    metrics.classification_end_time        = finalattributes['classification_end_time']
    metrics.classification_proc_time       = finalattributes['classification_process_time']
    metrics.attributeextraction_start_time = finalattributes['attributeextraction_start_time']
    metrics.attributeextraction_end_time   = finalattributes['attributeextraction_end_time']
    metrics.attributeextraction_proc_time  = finalattributes['attributeextraction_process_time']
    metrics.finalization_start_time        = finalattributes['finalization_start_time']
    metrics.finalization_end_time          = finalattributes['finalization_end_time']
    metrics.finalization_process_time      = finalattributes['finalization_process_time']
    db_context.session.add(metrics)
    try:
        db_context.session.commit()
    except:
        db_context.session.rollback()
        raise LookupError("Error while writing record to etmfa_document_metrics to DB for ID: {}".format(finalattributes['id']))


    attributes                             = Documentattributes()
    attributes.id                          = finalattributes['id']
    attributes.doc_comp_conf               = finalattributes['document_composite_confidence']
    attributes.customer                    = finalattributes['customer']
    attributes.protocol                    = finalattributes['protocol']
    attributes.country                     = finalattributes['country']
    attributes.site                        = finalattributes['site']
    attributes.doc_class                   = finalattributes['document_class']
    attributes.doc_date                    = finalattributes['document_date']
    attributes.doc_date_conf               = finalattributes['document_date_confidence']
    attributes.doc_date_type               = finalattributes['document_date_type']
    attributes.doc_classification          = finalattributes['document_classification']
    attributes.doc_classification_conf     = finalattributes['document_classification_confidence']
    attributes.name                        = finalattributes['name']
    attributes.name_conf                   = finalattributes['name_confidence']
    attributes.doc_subclassification       = finalattributes['document_subclassification']
    attributes.doc_subclassification_conf  = finalattributes['document_subclassification_confidence']
    attributes.subject                     = finalattributes['subject']
    attributes.subject_conf                = finalattributes['subject_confidence']
    attributes.language                    = finalattributes['language']
    attributes.language_conf               = finalattributes['language_confidence']
    attributes.alcoac_check_comp_score     = finalattributes['alcoac_check_composite_score']
    attributes.alcoac_check_comp_score_conf= finalattributes['alcoac_check_composite_score_confidence']
    attributes.alcoal_check_error          = finalattributes['alcoac_check_error']
    attributes.blinded                     = False
    #attributes.datetimecreated             = ' '
    attributes.doc_rejected                = ' '
    attributes.priority                    = finalattributes['priority']
    attributes.received_date               = finalattributes['received_date']
    attributes.site_personnel_list         = finalattributes['site_personnel_list']
    attributes.tmf_environment             = finalattributes['tmf_environment']
    attributes.tmf_ibr                     =  finalattributes['tmf_ibr']

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
    resource.error_reason = errorDict['error_message']
    resource.status = StatusEnum.ERROR

    resource.is_processing = False
    resource.last_updated = datetime.utcnow()

    db_context.session.commit()

    errorDict['error_message'] = errorDict['error_message']
    errorDict.pop('error_message', None) # 'message' is a keyword in the logger that cannot be overwritten

    logger.warn('A formatting error has occured for id: {}'.format(errorDict['id']), extra=errorDict)



def save_doc_feedback(_id, feedbackdata):

    recordfound = get_doc_resource_by_id(_id)

    resource = Documentfeedback()

    #feedbackdata = json.load(file)
    resource.p_id = str(int((datetime.now().timestamp()) * 1000000))
    resource.id = feedbackdata['id']
    resource.feedback_source = feedbackdata['feedback_source']
    resource.customer        = feedbackdata['customer']
    resource.protocol        = feedbackdata['protocol']
    resource.country         = feedbackdata['country']
    resource.site            = feedbackdata['site']
    resource.document_class  = feedbackdata['document_class']
    resource.document_date   = feedbackdata['document_date']
    resource.document_classification = feedbackdata['document_classification']
    resource.name            = feedbackdata['name']
    resource.language = feedbackdata['language']
    resource.document_rejected = feedbackdata['document_rejected']
    resource.attribute_auxillary_list = str(feedbackdata['attribute_auxillary_list'])


    db_context.session.add(resource)
    db_context.session.commit()

    return resource.as_dict()




def save_doc_processing(request, _id, doc_path):
    resource = DocumentProcess.from_post_request(request, _id, doc_path)

    resource.document_file_path = doc_path
    resource.Percent_complete = '0'
    resource.status = StatusEnum.TRIAGE_STARTED
    db_context.session.add(resource)
    db_context.session.commit()

    return resource.as_dict()


def received_formatting_error_event(errorDict):
    resource = get_doc_resource_by_id(errorDict['id'])

    # Update status
    resource.error_code = 1 # Doesn't mean anything
    resource.error_reason = errorDict['message']
    resource.status = StatusEnum.ERROR

    resource.is_processing = False
    resource.last_updated = datetime.utcnow()

    db_context.session.commit()

    errorDict['reason'] = errorDict['message']
    errorDict.pop('message', None) # 'message' is a keyword in the logger that cannot be overwritten

    logger.warn('A formatting error has occured for id: {}'.format(errorDict['id']), extra=errorDict)



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
    #else:
    #    logger.info("Resource found")
    return resource

def upsert_processing_metric(doc_processing_id, property_name, val):
    """Adds or updates a name-value pair of a metric, referenced by a processing resource.
    
    Args:
        doc_processing_id (int): Doc processing resource id
        property_name (str): Metric field name
        val (int): Metric value
    """
    doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
    metric = Metric.query.filter(Metric.document_processing_id==doc_processing_resource.p_id).first()

    if metric == None:
        metric = Metric(doc_processing_resource.p_id)

    processing_metric = processingMetric(metric.id, property_name, val)
    formatting_metric = FormattingMetric(metric.id, 'test', 'test')
    metric.processing_metrics.append(processing_metric)

    db_context.session.add(metric)
    db_context.session.commit()

def get_metrics_dict(doc_processing_id):
    doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
    metric = Metric.query.filter(Metric.document_processing_id == doc_processing_resource.p_id).first()
    #m_dict = {'DocumentProcessing_metrics': [], 'formatting_metrics': []
    m_dict = {'DocumentProcessing_metrics': []}

    if metric == None:
        return m_dict

    if metric.documentprocessing_metrics != None:
        m_dict['DocumentProcessing_metrics'] = [{'name': m.name, 'val': m.value} for m in metric.documentprocessing_metrics]
    
    # if metric.formatting_metrics != None:
    #     m_dict['formatting_metrics'] = [{'name': m.name, 'val': m.value} for m in metric.formatting_metrics]

    return m_dict    

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

    if doc_processing_resource == None:
        raise LookupError("No resource was found in DB for ID: {}".format(id))
    else:
        setattr(doc_processing_resource, namekey, value)
        db_context.session.commit()

def get_attributevalue(doc_processing_id, keydict):
        doc_processing_resource = get_doc_attributes_by_id(doc_processing_id)
        #metadata = IQMetadata.query.filter(IQMetadata.document_processing_id == doc_processing_resource.p_id)

        m_dict = {'metadata': []}
        if doc_processing_resource == None:
            raise LookupError("No resource was found in DB for ID: {}".format(id))
            return m_dict

        # m_dict = {'metadata': []}
        # if metadata == None:
        #     return m_dict
        else:
            for m in keydict:

                m_dict['metadata'].append({'name': m.name, 'val': getattr(doc_processing_resource,name)})

            return m_dict

    # # Make sure name doesn't already exist
    # metadata = IQMetadata.query.filter(IQMetadata.name==name).first()
    #
    #
    # if not metadata:
    #     # Create
    #     metadata = IQMetadata(doc_processing_id, name, value)
    #     doc_processing_resource.iq_metadata.append(metadata)
    # else:
    #     # Update
    #     metadata.value = value

def get_attribute_dict(doc_processing_id):
    doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
    #metadata = IQMetadata.query.filter(IQMetadata.document_processing_id==doc_processing_resource.p_id)

    if doc_processing_resource == None:
        raise LookupError("No resource was found in DB for ID: {}".format(id))

    return doc_processing_resource


def get_metadata_dict(doc_processing_id):
    doc_processing_resource = get_doc_resource_by_id(doc_processing_id)
    metadata = IQMetadata.query.filter(IQMetadata.document_processing_id==doc_processing_resource.p_id)

    m_dict = {'metadata': []}
    if metadata == None:
        return m_dict

    for m in metadata:
        m_dict['metadata'].append({'name': m.name, 'val': m.value})

    return m_dict

