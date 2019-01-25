from flask_restplus import Namespace, Resource, fields, reqparse, abort
import werkzeug

from ..api import api
from ...db.status import StatusEnum

object_links = api.model(' Resource Links', {
        # 'resource': fields.Url('api.resource_get_ep', 
        #     description='API URI for the main document translation resource.'),
        # 'target_file': fields.Url('api.formatted_doc_ep',
        #     description='API URI for the target translated document.'),
        # 'xliff_file': fields.Url('api.xliff_ep',
        #     description='API URI for the translated XLIFF file.'),
    })

kv_pair_model = api.model(' KeyValue Pair',{
            'name': fields.String(description='The metadata object supports dictionary style properties of any number of key-value pairs. ' +
                'Each metadata dictionary will be returned alongside the REST resource.'),
            'val': fields.String()
            })

supporting_docs_get = api.model('Supporting documents', {
    'id': fields.Integer(readOnly=True),
    'description': fields.String(readOnly=True),
    'file_path': fields.String(readOnly=True),
    })

status_model = api.model(' Document Translation Status', {
        'level': fields.String(),
        'status': fields.String()
    })

formatting_metrics = api.model(' Formatting metrics', {
        'name': fields.String(),
        'val': fields.String(),
    })

translation_metrics = api.model(' Translation metrics', {
        'name': fields.String(),
        'val': fields.String()
    })

metrics = api.model(' Metrics', {
        'formatting_metrics': fields.List(fields.Nested(formatting_metrics)),
        'translation_metrics': fields.List(fields.Nested(translation_metrics)),
    })

metadata_post = api.model('Translation resource metadata dictionary', {
        'metadata': fields.List(fields.Nested(kv_pair_model)),  
    })


# TODO:  Move this to models area and map to API object
StatusDict_desc = [s.value for s in StatusEnum]
StatusDict_keys = [s.name for s in StatusEnum]
StatusDict = dict(zip(StatusDict_keys, StatusDict_desc))
status_model = api.model('Document Translation object status', {
        'id': fields.Integer(readOnly=True, description='The linear id value of the current processing step.',
            default=StatusEnum.CREATED.value),
        'description': fields.String(readOnly=True, description='The description of the current document translation step.',
            default=StatusEnum.CREATED.name),
    })


document_translate_object_get = api.model('Document REST object',
    {
        'id': fields.String(readOnly=True, 
            description='The unique identifier (UUID) of a document translation job.'),
        'is_processing': fields.Boolean(readOnly=True, 
            description='The document is being formatted or translated. The XLIFF file or final documents may not exist.'),
        'is_deleted': fields.Boolean(readOnly=True, 
            description='The document processing request has been canceled.'),
        'file_name': fields.String(readOnly=True, 
            description='The name of the original file to translate'),
        'source_lang_short': fields.String(readOnly=True, 
            description='Source language description abbreviation'),
        'target_lang_short': fields.String(readOnly=True, 
            description='Target language description abbreviation'),
        'error_code': fields.String(readOnly=True, 
            description='Error code corresponding to any process error during formatting or translation.' +
            ' Empty error codes corrspond to no errors.'),
        'error_reason': fields.String(readOnly=True, 
            description='If an error code is present, an attempt will be made to supply a user-friendly error reason.'),
        'time_created': fields.DateTime,
        'last_updated': fields.DateTime,
        'links': fields.Nested(
            object_links,
            description='Logical API links to underlying REST objects.'
        ),
        'metadata': fields.List(fields.Nested(kv_pair_model)),
        'metrics': fields.Nested(metrics),
        'status': fields.Nested(status_model),
    }
)

supporting_docs_post = reqparse.RequestParser()
supporting_docs_post.add_argument('description',  
                         type=str,
                         required=True, 
                         help='Short description of document')
supporting_docs_post.add_argument('file',  
                         type=werkzeug.datastructures.FileStorage, 
                         location='files', 
                         required=True, 
                         help='Input document')


document_translate_object_post = reqparse.RequestParser()
document_translate_object_post.add_argument('file_name',  
                         type=str,
                         required=True, 
                         help='Input document name')
document_translate_object_post.add_argument('source_lang_short',  
                         type=str, 
                         required=True, 
                         help='Source language description abbreviation')
document_translate_object_post.add_argument('target_lang_short',  
                         type=str,
                         required=True, 
                         help='Target language description abbreviation')
document_translate_object_post.add_argument('file',  
                         type=werkzeug.datastructures.FileStorage, 
                         location='files', 
                         required=True, 
                         help='Input document')

document_translate_object_put = reqparse.RequestParser()
document_translate_object_put.add_argument('file',  
                         type=werkzeug.datastructures.FileStorage, 
                         location='files', 
                         required=True, 
                         help='Document translation XLIFF file')
document_translate_object_put.add_argument('cache',
                        type=bool,
                        required=False,
                        help='Cache the segments from the Xliff for future machine translation.',
                        default=True)

final_document_translate_object_post = reqparse.RequestParser()
final_document_translate_object_post.add_argument('file',  
                         type=werkzeug.datastructures.FileStorage, 
                         location='files', 
                         required=True, 
                         help='Final edited document')


language_pair = api.model('An available language pair for document translation', {
    'source_lang_short': fields.String(readOnly=True, description='The source language abbreviation used in a document tranlsation request'),
    'source_lang_description': fields.String(readOnly=True, description='The source language description'),
    'target_lang_short': fields.String(readOnly=True, description='The target language abbreviation used in a document tranlsation request'),
    'target_lang_description': fields.String(readOnly=True, description='The target language description'),
})