from flask_restplus import Namespace, Resource, fields, reqparse, abort
import werkzeug

from ..api import api


kv_pair_model = api.model(' KeyValue Pair for patch ',{
            'name': fields.String(description='The metadata object supports dictionary style properties of any number of key-value pairs. ' +
                'Each metadata dictionary will be returned alongside the REST resource.'),
            'val': fields.String()
})
k_pair_model = api.model(' Key for attributes',{
            'name': fields.String(description='The metadata object supports dictionary style properties of any number of key-value pairs. ' +
                'Each metadata dictionary will be returned alongside the REST resource.'),
            #'val': fields.String()
})

metadata_post = api.model('Document attributes patch model', {
        'metadata': fields.List(fields.Nested(kv_pair_model)),
    })

metadata_get = api.model('eTMFA attribute extraction get attributes', {
     'metadata': fields.List(fields.Nested(k_pair_model))
 })


eTMFA_object_get = api.model('Document Processing Status Model',
    {
        'id': fields.String(readOnly=True, 
            description='The unique identifier (UUID) of eTMFA document.'),
        'isProcessing': fields.Boolean(readOnly=True,
            description='The document is being processed. Final attributes of documents may not exist.'),
        'percentComplete': fields.String(readOnly=True,
            description='The percentage of document is being processed. Final attributes of documents will be ready when percentage is 100.'),
        'fileName': fields.String(readOnly=True,
            description='The name of the original eTMF file to automate'),
        'documentFilePath': fields.String(readOnly=True,
            description='The name of the original eTMF file location shared in DFS'),
        'errorCode': fields.String(readOnly=True,
            description='Error code corresponding to any process error during TMF document automation.' +
            ' Empty error codes corrspond to no errors.'),
        'errorReason': fields.String(readOnly=True,
            description='If an error code is present, an attempt will be made to supply a user-friendly error reason.'),
        'timeCreated': fields.DateTime,
        'lastUpdated': fields.DateTime,
        'status': fields.String(readOnly=True,
            description='Document processing stage (triage/ocr/classifier/extractor/finalizer'),
    }
)

eTMFA_object_get_status = api.model('Document Processing Status Model',
    {
        'id': fields.String(readOnly=True,
            description='The unique identifier (UUID) of eTMFA document.'),
        'isProcessing': fields.Boolean(readOnly=True,
            description='The document is being processed. Final attributes of documents may not exist.'),
        'percentComplete': fields.String(readOnly=False,
            description='The percentage of document is being processed. Final attributes of documents will be ready when percentage is 100.'),
        'status': fields.String(readOnly=False,
            description='Processing document stage (triage/ocr/classifier/xtractor/finalizer)'),
        'fileName': fields.String(readOnly=True,
            description='The name of the original eTMF file to automate'),
        'documentFilePath': fields.String(readOnly=True,
            description='The path of the original eTMF file to automate'),
        'errorCode': fields.String(readOnly=True,
            description='Error code corresponding to any process error during TMF document automation.' +
            ' Empty error codes corrspond to no errors.'),
        'errorReason': fields.String(readOnly=True,
            description='If an error code is present, an attempt will be made to supply a user-friendly error reason.'),
        'timeCreated': fields.DateTime,
        'lastUpdated': fields.DateTime,
    }
)


eTMFA_metrics_get = api.model('Document Processing Metrics Model',
    {
        'id': fields.String(readOnly=True,
            description='The unique identifier (UUID) of eTMFA document.'),
        'totalProcessTime': fields.String(readOnly=True,
            description='total processing time of eTMFA document.'),
        'queueWaitTime': fields.String(readOnly=True,
            description='total queue wait time of eTMFA document.'),
        'triageMachineName':fields.String(readOnly=True,
            description='Triage machine name where service is running'),
        'triageVersion':fields.String(readOnly=True,
            description='Triage code version'),
        'triageStartTime':fields.String(readOnly=True,
            description='Triage Start time in Server'),
        'triageEndTime':fields.String(readOnly=True,
            description='Triage end time in Server'),
        'triageProcTime':fields.String(readOnly=True,
            description='Triage total processing time per document in Server'),
        'digitizerMachineName': fields.String(readOnly=True,
            description='digitizer machine name where service is running'),
        'digitizerVersion': fields.String(readOnly=True,
            description='digitizer code version'),
        'digitizerStartTime':fields.String(readOnly=True,
            description='Digitizer start time in Server'),
        'digitizerEndTime':fields.String(readOnly=True,
            description='Digitizer end time in Server'),
        'digitizerProcTime':fields.String(readOnly=True,
            description='Digitizer total processing time per document in Server'),
        'classificationMachineName': fields.String(readOnly=True,
            description='classification machine name where service is running'),
        'classificationVersion': fields.String(readOnly=True,
            description='classification code version'),
        'classificationStartTime':fields.String(readOnly=True,
            description='classification start time in Server'),
        'classificationEndTime':fields.String(readOnly=True,
            description='classification end time in Server'),
        'classificationProcTime':fields.String(readOnly=True,
            description='classification total processing time per document in Server'),
        'attExtractionMachineName': fields.String(readOnly=True,
            description='attribute extraction machine name where service is running'),
        'attExtractionVersion': fields.String(readOnly=True,
            description='attribute extraction code version'),
        'attExtractionStartTime':fields.String(readOnly=True,
            description='attribute extraction start time in Server'),
        'attExtractionEndTime':fields.String(readOnly=True,
            description='attribute extraction end time in Server'),
        'attExtractionProcTime':fields.String(readOnly=True,
            description='attribute extraction total processing time per document in Server'),
        'finalizationMachineName': fields.String(readOnly=True,
            description='finalization machine name where service is running'),
        'finalizationVersion': fields.String(readOnly=True,
            description='finalization code version'),
        'finalizationStartTime':fields.String(readOnly=True,
            description='finalization start time in Server'),
        'finalizationEndTime':fields.String(readOnly=True,
            description='finalization end time in Server'),
        'docType':fields.String(readOnly=True,
            description='Type of the document processed digitized/scanned'),
        'docTypeOriginal': fields.String(readOnly=True,
            description='Type of original document uploaded'),
        'docSegments': fields.String(readOnly=True,
            description='Number of segments processed in the document'),
        'docPages': fields.String(readOnly=True,
            description='Number of pages in the document'),
        'timeCreated': fields.String(readOnly=True,
            description='Time document resource processed'),
    }
)


eTMFA_attributes_get = api.model('Document Processing Attributes Model',
    {
        'id': fields.String(readOnly=True,
            description='The unique identifier (UUID) of eTMFA document.'),
        'fileName': fields.String(readOnly=True,
            description='Name of the document processed.'),
        'documentFilePath': fields.String(readOnly=True,
            description='Document location processed.'),
        'customer' : fields.String(readOnly=True,
            description = 'customer name'),
        'protocol' : fields.String(readOnly=True,
            description = 'protocol'),
        'country' : fields.String(readOnly=True,
            description = 'country'),
        'site' : fields.String(readOnly=True,
            description = 'site'),
        'docClass' : fields.String(readOnly=True,
            description = 'document class'),
        'unblinded': fields.Boolean(readOnly=True,
            description='document is blinded or not'),
        'priority': fields.String(readOnly=True,
            description='priority'),
        'receivedDate': fields.String(readOnly=True,
            description='date document received'),
        'sitePersonnelList': fields.String(readOnly=True,
            description='site personnel list'),
        'tmfEnvironment': fields.String(readOnly=True,
            description='tmf environment'),
        'tmfIbr': fields.String(readOnly=True,
            description='tmf/ibr environment'),

        'docCompConf': fields.String(readOnly=True,
            description='Classification confidence of document processed'),
        'docClassification': fields.String(readOnly=True,
            description='document class'),
        'docClassificationConf': fields.String(readOnly=True,
            description='document class'),
        'docDate' : fields.String(readOnly=True,
            description = 'document date'),
        'docDateConf' : fields.String(readOnly=True,
            description = 'document date confidence'),
        'docDateType' : fields.String(readOnly=True,
            description = 'document date type'),
        'name' : fields.String(readOnly=False,
            description = 'name'),
        'nameConf' : fields.String(readOnly=True,
            description = 'name confidence'),
        'language': fields.String(readOnly=True,
            description='language'),
        'languageConf': fields.String(readOnly=True,
            description='language confidence'),
        'subject': fields.String(readOnly=True,
            description='subject'),
        'subjectConf': fields.String(readOnly=True,
            description='subject confidence'),
        'alcoacCheckError': fields.String(readOnly=True,
            description='alcoac check error'),
        'alcoacCheckCompScore': fields.String(readOnly=True,
            description='Alcoac check composite score'),
        'alcoacCheckCompScoreConf': fields.String(readOnly=True,
            description='alcoac check composite score confidence'),
        'docClassificationElvis': fields.String(readOnly=True,
            description='document classification_elvis'),

        'docSubclassification' : fields.String(readOnly=True,
            description = 'document subclassification'),
        'docSubclassificationConf' : fields.String(readOnly=True,
            description = 'document subclassification confidence'),
        'attributeAuxillaryList': fields.String(readOnly=True,
            description = 'Attribute auxillary list values'),
        'documentRejected' : fields.String(readOnly=True,
            description = 'document rejected'),
        'timeCreated': fields.String(readOnly=True,
            description='date time created'),

    }
)


eTMFA_object_post = reqparse.RequestParser()
eTMFA_object_post.add_argument('fileName',
                         type=str,
                         help='Input document name')
eTMFA_object_post.add_argument('customer',
                         type=str, 
                         required=True,
                         help='Customer Name')
eTMFA_object_post.add_argument('protocol',
                         type=str,
                         required=True,
                         help='Protocol')
eTMFA_object_post.add_argument('country',
                         type=str,
                         required=False,
                         help='Country')
eTMFA_object_post.add_argument('site',
                         type=str,
                         required=False,
                         help='Site')
eTMFA_object_post.add_argument('documentClass',
                         type=str,
                         required=True,
                         help='Document Class(core/country/site)')
eTMFA_object_post.add_argument('tmfIbr',
                         type=str,
                         required=False,
                         help='TMF/IBR')
eTMFA_object_post.add_argument('unblinded',
                         type=bool,
                         required=False,
                         help='Unblinded')
eTMFA_object_post.add_argument('tmfEnvironment',
                         type=str,
                         required=False,
                         help='TMF Environment')
eTMFA_object_post.add_argument('receivedDate',
                         type=str,
                         required=False,
                         help='Received Date')
eTMFA_object_post.add_argument('sitePersonnelList',
                         type=str,
                         required=False,
                         help='Site personnel Information')
eTMFA_object_post.add_argument('priority',
                         type=str,
                         required=False,
                         help='Priority')
eTMFA_object_post.add_argument('file',
                         type=werkzeug.datastructures.FileStorage, 
                         location='files', 
                         required=True, 
                         help='Input document')


document_processing_object_put = api.model('Document feedback definition',
    {
        'id': fields.String(required=True,
                description='The unique identifier (UUID) of a document processing job.'),
        'feedbackSource': fields.String(required=True,
                description='Feedback source for the processed document'),
        'customer': fields.String(required=True,
                description='Customer'),
        'protocol': fields.String(required=True,
                description='protocol'),
        'country': fields.String(required=True,
                description='country'),
        'site': fields.String(required=True,
                description='site'),
        'documentClass': fields.String(required=True,
                description='document class'),
        'documentDate': fields.String(required=True,
                description='date string yyyymmdd'),
        'documentClassification': fields.String(required=True,
                description='document classification'),
        'name': fields.String(required=True,
                description='name'),
        'language': fields.String(required=True,
                description='language'),
        'documentRejected': fields.Boolean(readOnly=True,
            description='document rejected'),
        'attributeAuxillaryList': fields.List(fields.Nested(kv_pair_model)),
})


document_processing_object_put_get = api.model('Document Processing Feedback Model',
    {
        'id': fields.String(readOnly=True,
            description='The unique identifier (UUID) of a document processing job.'),
        'fileName': fields.String(readOnly=True,
            description='file name of the document for updating feedback'),
        'documentFilePath': fields.String(readOnly=True,
            description='path of the document for updating feedback'),
        'feedbackSource': fields.String(readOnly=True,
            description='Feedback source for the processed document'),
        'customer': fields.String(readOnly=True,
            description='Customer'),
        'protocol': fields.String(readOnly=True,
            description='protocol'),
        'country': fields.String(readOnly=True,
            description='country'),
        'site': fields.String(readOnly=True,
            description='site'),
        'documentClass': fields.String(readOnly=True,
            description='document class'),
        'documentDate': fields.String(readOnly=True,
            description='date string yyyymmdd'),
        'documentClassification': fields.String(readOnly=True,
            description='document classification'),
        'name': fields.String(readOnly=True,
            description='name'),
        'language': fields.String(readOnly=True,
            description='language'),
        'documentRejected': fields.Boolean(readOnly=True,
            description='document rejected'),
        'attributeAuxillaryList': fields.String(readOnly=True,
            description='Attribute auxillary list'),
    }
)
