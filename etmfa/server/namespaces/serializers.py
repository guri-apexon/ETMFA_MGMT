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
k_pair_model = api.model(' KeyValue Pair',{
            'name': fields.String(description='The metadata object supports dictionary style properties of any number of key-value pairs. ' +
                'Each metadata dictionary will be returned alongside the REST resource.')
            #'val': fields.String()
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

documentprocessing_metrics = api.model(' Document Processing metrics', {
        'name': fields.String(),
        'val': fields.String(),
    })

metrics = api.model(' Metrics', {
        'documentprocessing_metrics': fields.List(fields.Nested(documentprocessing_metrics)),
        #'translation_metrics': fields.List(fields.Nested(translation_metrics)),
    })

metadata_post = api.model('Translation resource metadata dictionary', {
        'metadata': fields.List(fields.Nested(kv_pair_model)),
    })
metadata_get = api.model('eTMFA attribute extraction metadata dictionary', {
     'metadata': fields.List(fields.Nested(k_pair_model))
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


eTMFA_object_get = api.model('Document REST object',
    {
        'id': fields.String(readOnly=True, 
            description='The unique identifier (UUID) of eTMFA document.'),
        'is_processing': fields.Boolean(readOnly=True, 
            description='The document is being processed. Final attributes of documents may not exist.'),
        'Percent_complete': fields.String(readOnly=True,
            description='The percentage of document is being processed. Final attributes of documents will be ready when percentage is 100.'),
        'file_name': fields.String(readOnly=True,
            description='The name of the original eTMF file to automate'),
        'error_code': fields.String(readOnly=True,
            description='Error code corresponding to any process error during TMF document automation.' +
            ' Empty error codes corrspond to no errors.'),
        'error_reason': fields.String(readOnly=True, 
            description='If an error code is present, an attempt will be made to supply a user-friendly error reason.'),
        'time_created': fields.DateTime,
        'last_updated': fields.DateTime,
        'status': fields.Nested(status_model),
    }
)

eTMFA_object_get_status = api.model('Document REST object',
    {
        'id': fields.String(readOnly=True,
            description='The unique identifier (UUID) of eTMFA document.'),
        'is_processing': fields.Boolean(readOnly=True,
            description='The document is being processed. Final attributes of documents may not exist.'),
        'Percent_complete': fields.String(readOnly=False,
            description='The percentage of document is being processed. Final attributes of documents will be ready when percentage is 100.'),
        'status': fields.Nested(status_model),
        'file_name': fields.String(readOnly=True,
            description='The name of the original eTMF file to automate'),
        'document_file_path': fields.String(readOnly=True,
            description='The path of the original eTMF file to automate'),
        'error_code': fields.String(readOnly=True,
            description='Error code corresponding to any process error during TMF document automation.' +
            ' Empty error codes corrspond to no errors.'),
        'error_reason': fields.String(readOnly=True,
            description='If an error code is present, an attempt will be made to supply a user-friendly error reason.'),
        'time_created': fields.DateTime,
        'last_updated': fields.DateTime,
    }
)


eTMFA_attributes_get = api.model('Document REST object',
    {
        'id': fields.String(readOnly=True,
            description='The unique identifier (UUID) of eTMFA document.'),
        'doc_comp_conf': fields.String(readOnly=True,
            description = 'Classification confidence of document processed'),
        'customer' : fields.String(readOnly=True,
            description = 'customer name'),
        'protocol' : fields.String(readOnly=True,
            description = 'protocol'),
        'country' : fields.String(readOnly=True,
            description = 'country'),
        'site' : fields.String(readOnly=True,
            description = 'site'),
        'doc_class' : fields.String(readOnly=True,
            description = 'document class'),
        'doc_date' : fields.String(readOnly=True,
            description = 'document date'),
        'doc_date_conf' : fields.String(readOnly=True,
            description = 'document date confidence'),
        'doc_date_type' : fields.String(readOnly=True,
            description = 'document date type'),
        'doc_classification' : fields.String(readOnly=True,
            description = 'document class'),
        'doc_classification_conf' : fields.String(readOnly=True,
            description = 'document class'),
        'name' : fields.String(readOnly=True,
            description = 'name'),
        'name_conf' : fields.String(readOnly=True,
            description = 'name confidence'),
        'doc_subclassification' : fields.String(readOnly=True,
            description = 'document subclassification'),
        'doc_subclassification_conf' : fields.String(readOnly=True,
            description = 'document subclassification confidence'),
        'attribute_auxillary_list': fields.List(fields.Nested(kv_pair_model)),
        'subject' : fields.String(readOnly=True,
            description = 'subject'),
        'subject_conf' : fields.String(readOnly=True,
            description = 'subject confidence'),
        'language' : fields.String(readOnly=True,
            description = 'language'),
        'language_conf' : fields.String(readOnly=True,
            description = 'language confidence'),
        'alcoac_check_comp_score' : fields.String(readOnly=True,
            description = 'Alcoac check composite score'),
        'alcoac_check_comp_score_conf' : fields.String(readOnly=True,
            description = 'alcoac check composite score confidence'),
        'alcoal_check_error' : fields.String(readOnly=True,
            description = 'alcoac check error'),
        'blinded': fields.Boolean(readOnly=True,
            description='document is blinded or not'),
        'datetimecreated' : fields.String(readOnly=True,
            description = 'date time created'),
        'document_rejected' : fields.String(readOnly=True,
            description = 'document rejected'),
        'priority' : fields.String(readOnly=True,
            description = 'priority'),
        'received_date' : fields.String(readOnly=True,
            description = 'date document received'),
        'site_personnel_list' : fields.String(readOnly=True,
            description = 'site personnel list'),
        'tmf_environment' : fields.String(readOnly=True,
            description = 'tmf environment'),
        'tmf_ibr' : fields.String(readOnly=True,
            description = 'tmf/ibr environment'),

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


eTMFA_object_post = reqparse.RequestParser()
eTMFA_object_post.add_argument('file_name',
                         type=str,
                         #required=True,
                         help='Input document name')
eTMFA_object_post.add_argument('Customer',
                         type=str, 
                         required=True, 
                         help='Customer Name')
eTMFA_object_post.add_argument('Protocol',
                         type=str,
                         required=True, 
                         help='Protocol')
eTMFA_object_post.add_argument('Country',
                         type=str,
                         required=False,
                         help='Country')
eTMFA_object_post.add_argument('Site',
                         type=str,
                         required=False,
                         help='Site')
eTMFA_object_post.add_argument('Document_Class',
                         type=str,
                         required=True,
                         help='Document_Class')
eTMFA_object_post.add_argument('TMF_IBR',
                         type=str,
                         required=True,
                         help='TMF_IBR')
eTMFA_object_post.add_argument('Blinded',
                         type=bool,
                         required=False,
                         help='Blinded')
eTMFA_object_post.add_argument('TMF_Environment',
                         type=str,
                         required=True,
                         help='TMF_Environment')
eTMFA_object_post.add_argument('Received_Date',
                         type=str,
                         required=True,
                         help='Received_Date')
eTMFA_object_post.add_argument('site_personnel_list',
                         type=str,
                         required=True,
                         help='site_personnel_list')
eTMFA_object_post.add_argument('Priority',
                         type=str,
                         required=True,
                         help='Priority')
eTMFA_object_post.add_argument('file',
                         type=werkzeug.datastructures.FileStorage, 
                         location='files', 
                         required=True, 
                         help='Input document')

document_processing_object_put = reqparse.RequestParser()
# document_processing_object_put.add_argument('id',
#                         type= str,
#                         required=True,
#                         help='ID of the document processed to give feedback information after manual evaluation')
document_processing_object_put.add_argument('file',
                         type=werkzeug.datastructures.FileStorage,
                         location='files',
                         required=True,
                         help='Feedback information for the document processed with given id number')

document_processing_object_put_get = api.model('Document REST object',
    {
        'id': fields.String(readOnly=True,
            description='The unique identifier (UUID) of a document processing job.'),
        'feedback_source': fields.String(readOnly=True,
            description='Feedback source for the processed document'),
        'customer': fields.String(readOnly=True,
            description='Customer'),
        'protocol': fields.String(readOnly=True,
            description='protocol'),
        'country': fields.String(readOnly=True,
            description='country'),
        'site': fields.String(readOnly=True,
            description='site'),
        'document_class': fields.String(readOnly=True,
            description='document class'),
        'document_date': fields.String(readOnly=True,
            description='date string yyyymmdd'),
        'document_classification': fields.String(readOnly=True,
            description='document classification'),
        'name': fields.String(readOnly=True,
            description='name'),
        'language': fields.String(readOnly=True,
            description='language'),
        'document_rejected': fields.Boolean(readOnly=True,
            description='document rejected'),
        'attribute_auxillary_list': fields.List(fields.Nested(kv_pair_model)),
    }
)





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