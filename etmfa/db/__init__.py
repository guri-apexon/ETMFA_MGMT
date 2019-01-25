import os, logging, time, json, requests
import pandas as pd

from datetime import datetime
from flask_migrate import Migrate
from lxml import html

# Global DB context must be initialized before local imports
from .db import db_context

from ..consts import Consts as consts
logger = logging.getLogger(consts.LOGGING_NAME)

# Import all models for table creation
from .models.processing import Processing
from .models.documenttranslate import DocumentTranslate
from .models.metric import Metric
from .models.translationmetric import TranslationMetric
from .models.formattingmetric import FormattingMetric
from .models.metadata import IQMetadata
from .models.supportingdoc import SupportingDoc

from .status import StatusEnum
from ..messaging.models.translation_request import TranslationRequest

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

def save_doc_translate(request, _id, doc_path, get_langs_uri):
    resource = DocumentTranslate.from_post_request(request, _id, doc_path)

    # validate params
    lang_pairs = get_valid_lang_pairs(get_langs_uri)
    is_valid_pair = any(filter(lambda lp: lp['source_lang_short'] == resource.source_lang_short and
                                    lp['target_lang_short'] == resource.target_lang_short,
                                    lang_pairs))

    if not is_valid_pair:
        raise ValueError("Source language ('{}') and Target language ('{}') must be supported language pairs.".format(resource.source_lang_short, resource.target_lang_short))

    resource.status = StatusEnum.DECONSTRUCTION_STARTED
    db_context.session.add(resource)
    db_context.session.commit()
    return resource.as_dict()

def get_valid_lang_pairs(get_langs_uri):
    resp = requests.get(get_langs_uri, verify=False)
    return json.loads(resp.content)


def save_xliff_request(_id, xliff_path):
    resource = get_doc_resource_by_id(_id)

    resource.last_updated = datetime.utcnow()
    resource.is_processing = True
    resource.status = StatusEnum.RECONSTRUCTION_STARTED
    resource.edited_xliff_path = xliff_path
    db_context.session.commit()

    return resource.as_dict()

def received_deconstruction_event(id, xliff_path, message_publisher):
    resource = get_doc_resource_by_id(id)

    resource.deconstructed_xliff_path = xliff_path
    resource.status = StatusEnum.TRANSLATION_STARTED
    resource.last_updated = datetime.utcnow()
    db_context.session.commit()

    # Start translation request
    translation_req_msg = TranslationRequest(
        id,
        resource.source_lang_short,
        resource.target_lang_short,
        xliff_path
    )

    message_publisher.send_obj(translation_req_msg)

    return resource.as_dict()

def received_translated_complete_event(id, xliff_path, metrics_dict):
    resource = get_doc_resource_by_id(id)

    # Update translation xliff_location
    resource.is_processing = False
    resource.translated_xliff_path = xliff_path
    resource.status = StatusEnum.TRANSLATION_COMPLETED
    resource.last_updated = datetime.utcnow()

    # Update metrics
    for k, v in metrics_dict.items():
        upsert_translation_metric(resource.id, k, v)

    db_context.session.commit()

def received_reconstruction_complete_event(id, docPath):
    resource = get_doc_resource_by_id(id)

    # Update translation xliff_location
    resource.is_processing = False
    resource.formatted_doc_path = docPath
    resource.status = StatusEnum.RECONSTRUCTION_COMPLETED
    resource.last_updated = datetime.utcnow()
    db_context.session.commit()

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


def get_xliff_location_by_id(id):
    """
    Returns xliff path of corresponding resource
    """
    resource = get_doc_resource_by_id(id)
    return resource.deconstructed_xliff_path

def get_translated_xliff_location_by_id(id):
    """
    Returns xliff path of corresponding resource
    """
    resource = get_doc_resource_by_id(id)
    return resource.translated_xliff_path

def get_doc_translate_by_id(id, full_mapping=False):
    resource_dict = get_doc_resource_by_id(id).as_dict()

    if not full_mapping:
        return resource_dict

    resource_dict['metrics'] = get_metrics_dict(id)
    resource_dict['metadata'] = get_metadata_dict(id)['metadata']

    return resource_dict

def get_doc_resource_by_id(id):
    """
    Returns the DTO by id.
    Raises LookupError if no id is found.
    """

    resource = DocumentTranslate.query.filter(DocumentTranslate.id.like(str(id))).first()

    if resource == None:
        raise LookupError("No translation resource was found in DB for ID: {}".format(id))

    return resource

def upsert_translation_metric(doc_translate_id, property_name, val):
    """Adds or updates a name-value pair of a metric, referenced by a translation resource.
    
    Args:
        doc_translate_id (int): Doc translation resource id
        property_name (str): Metric field name
        val (int): Metric value
    """
    doc_trans_resource = get_doc_resource_by_id(doc_translate_id)
    metric = Metric.query.filter(Metric.document_translate_id==doc_trans_resource.p_id).first()

    if metric == None:
        metric = Metric(doc_trans_resource.p_id)

    trans_metric = TranslationMetric(metric.id, property_name, val)
    formatting_metric = FormattingMetric(metric.id, 'test', 'test')
    metric.translation_metrics.append(trans_metric)

    db_context.session.add(metric)
    db_context.session.commit()

def get_metrics_dict(doc_translate_id):
    doc_trans_resource = get_doc_resource_by_id(doc_translate_id)
    metric = Metric.query.filter(Metric.document_translate_id == doc_trans_resource.p_id).first()

    m_dict = {'translation_metrics': [], 'formatting_metrics': []}

    if metric == None:
        return m_dict

    if metric.translation_metrics != None:
        m_dict['translation_metrics'] = [{'name': m.name, 'val': m.value} for m in metric.translation_metrics]
    
    if metric.formatting_metrics != None:
        m_dict['formatting_metrics'] = [{'name': m.name, 'val': m.value} for m in metric.formatting_metrics]

    return m_dict    

def upsert_metadata(doc_translate_id, name, value):
    doc_trans_resource = get_doc_resource_by_id(doc_translate_id)

    # Make sure name doesn't already exist
    metadata = IQMetadata.query.filter(IQMetadata.name==name).first()
    if not metadata:
        # Create
        metadata = IQMetadata(doc_translate_id, name, value)
        doc_trans_resource.iq_metadata.append(metadata)
    else:
        # Update
        metadata.value = value

    db_context.session.add(doc_trans_resource)
    db_context.session.commit()

def get_metadata_dict(doc_translate_id):
    doc_trans_resource = get_doc_resource_by_id(doc_translate_id)
    metadata = IQMetadata.query.filter(IQMetadata.document_translate_id==doc_trans_resource.p_id)

    m_dict = {'metadata': []}
    if metadata == None:
        return m_dict

    for m in metadata:
        m_dict['metadata'].append({'name': m.name, 'val': m.value})

    return m_dict

def add_supporting_doc(doc_trans_id, file_path, description):
    doc_trans_resource = get_doc_resource_by_id(doc_trans_id)
    supporting_doc = SupportingDoc(doc_trans_resource.p_id, file_path, description)

    doc_trans_resource.supporting_docs.append(supporting_doc)

    db_context.session.add(doc_trans_resource)
    db_context.session.commit()
    
    return supporting_doc.as_dict()

def get_supporting_docs(doc_translate_id):
    doc_trans_resource = get_doc_resource_by_id(doc_translate_id)
    supporting_docs = SupportingDoc.query.filter(SupportingDoc.document_translate_id==doc_trans_resource.p_id)

    return {'supporting_docs': [s.as_dict() for s in supporting_docs]}


def delete_doctranslate_request(doc_translate_id):
    doc_trans_resource = get_doc_resource_by_id(doc_translate_id)
    doc_trans_resource.is_deleted = True
    doc_trans_resource.last_updated = datetime.utcnow()

    db_context.session.commit()

    return get_doc_translate_by_id(doc_translate_id, full_mapping=True)