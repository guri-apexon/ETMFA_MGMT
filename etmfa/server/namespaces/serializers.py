import werkzeug
from flask_restplus import fields, reqparse, inputs
from etmfa.server.api import api
from etmfa.workflow.messaging.models.document_class import DocumentClass

kv_pair_model = api.model(' KeyValue Pair for patch ', {
    'name': fields.String(
        description='The metadata object supports dictionary style properties of any number of key-value pairs. ' +
                    'Each metadata dictionary will be returned alongside the REST resource.'),
    'val': fields.String()
})
k_pair_model = api.model(' Key for attributes', {
    'name': fields.String(
        description='The metadata object supports dictionary style properties of any number of key-value pairs. ' +
                    'Each metadata dictionary will be returned alongside the REST resource.'),
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
                                                         description='Document processing stage (triage/dig1/dig2/omop/extractor/finalizer'),
                                 'qcStatus': fields.String(readOnly=True,
                                                         description='QC status (NOT started/QC1/QC2/Feedback run/completed)'),
                                 'runId': fields.Integer(readOnly=True, description='Feedback Run ID'),
                                 'workFlowName': fields.String(readOnly=True,
                                                         description='work flow name ')
                             }
                             )


PD_qc_get = api.model('Document Processing Status Model',
                      {
                          'aidocid': fields.String(readOnly=True,
                                                   description='The aidocid for QC update.'),
                          'qcApprovedBy': fields.String(readOnly=True,
                                                        description='The approved by user id.'),

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
                                        'workFlowName': fields.String(readOnly=True,
                                                                        description='work flow name ')

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
                                  'triageMachineName': fields.String(readOnly=True,
                                                                     description='Triage machine name where service is running'),
                                  'triageVersion': fields.String(readOnly=True,
                                                                 description='Triage code version'),
                                  'triageStartTime': fields.String(readOnly=True,
                                                                   description='Triage Start time in Server'),
                                  'triageEndTime': fields.String(readOnly=True,
                                                                 description='Triage end time in Server'),
                                  'triageProcTime': fields.String(readOnly=True,
                                                                  description='Triage total processing time per document in Server'),
                                  'digitizerMachineName': fields.String(readOnly=True,
                                                                        description='digitizer machine name where service is running'),
                                  'digitizerVersion': fields.String(readOnly=True,
                                                                    description='digitizer code version'),
                                  'digitizerStartTime': fields.String(readOnly=True,
                                                                      description='Digitizer start time in Server'),
                                  'digitizerEndTime': fields.String(readOnly=True,
                                                                    description='Digitizer end time in Server'),
                                  'digitizerProcTime': fields.String(readOnly=True,
                                                                     description='Digitizer total processing time per document in Server'),
                                  'classificationMachineName': fields.String(readOnly=True,
                                                                             description='classification machine name where service is running'),
                                  'classificationVersion': fields.String(readOnly=True,
                                                                         description='classification code version'),
                                  'classificationStartTime': fields.String(readOnly=True,
                                                                           description='classification start time in Server'),
                                  'classificationEndTime': fields.String(readOnly=True,
                                                                         description='classification end time in Server'),
                                  'classificationProcTime': fields.String(readOnly=True,
                                                                          description='classification total processing time per document in Server'),
                                  'attExtractionMachineName': fields.String(readOnly=True,
                                                                            description='attribute extraction machine name where service is running'),
                                  'attExtractionVersion': fields.String(readOnly=True,
                                                                        description='attribute extraction code version'),
                                  'attExtractionStartTime': fields.String(readOnly=True,
                                                                          description='attribute extraction start time in Server'),
                                  'attExtractionEndTime': fields.String(readOnly=True,
                                                                        description='attribute extraction end time in Server'),
                                  'attExtractionProcTime': fields.String(readOnly=True,
                                                                         description='attribute extraction total processing time per document in Server'),
                                  'finalizationMachineName': fields.String(readOnly=True,
                                                                           description='finalization machine name where service is running'),
                                  'finalizationVersion': fields.String(readOnly=True,
                                                                       description='finalization code version'),
                                  'finalizationStartTime': fields.String(readOnly=True,
                                                                         description='finalization start time in Server'),
                                  'finalizationEndTime': fields.String(readOnly=True,
                                                                       description='finalization end time in Server'),
                                  'docType': fields.String(readOnly=True,
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


eTMFA_attributes_input = reqparse.RequestParser()
eTMFA_attributes_input.add_argument('id',
                                    type=str,
                                    required=True,
                                    help='Source Input document name')
eTMFA_attributes_input.add_argument('protocolNumber',
                                    type=str,
                                    required=True,
                                    help='Protocol Number')
eTMFA_attributes_input.add_argument('projectId',
                                    type=str,
                                    required=True,
                                    help='Project ID')
eTMFA_attributes_input.add_argument('versionNumber',
                                    type=str,
                                    required=False,
                                    help='Version Number')
eTMFA_attributes_input.add_argument('amendment',
                                    type=str,
                                    required=False,
                                    help='Amendment')
eTMFA_attributes_input.add_argument('docStatus',
                                    type=str,
                                    required=True,
                                    help='Document Status')
eTMFA_attributes_input.add_argument('userId',
                                    type=str,
                                    required=False,
                                    help='User ID')
eTMFA_attributes_input.add_argument('environment',
                                    type=str,
                                    required=False,
                                    help='Environment')
eTMFA_attributes_input.add_argument('sourceSystem',
                                    type=str,
                                    required=False,
                                    help='Source System')
eTMFA_attributes_input.add_argument('requestType',
                                    type=str,
                                    required=False,
                                    help='Request Type')


# Latest protocol download file
latest_protocol_download_input = reqparse.RequestParser()
latest_protocol_download_input.add_argument(
    'protocolNumber', type=str, required=True, help='Protocol number')
latest_protocol_download_input.add_argument(
    'id', type=str, required=False, help='Unique PD ID of the document')
latest_protocol_download_input.add_argument(
    'approvalDate', type=str, required=False, help='Approval date of the document in YYYYMMDD format')
latest_protocol_download_input.add_argument(
    'versionNumber', type=str, required=False, help='Version Number')
latest_protocol_download_input.add_argument(
    'documentStatus', type=str, required=False, help='Document status, default is "final"')
latest_protocol_download_input.add_argument(
    'sourceSystem', type=str, required=False, help='Source system calling this API')

# Latest protocol contents
latest_protocol_contents_input = reqparse.RequestParser()
latest_protocol_contents_input.add_argument(
    'protocolNumber', type=str, required=True, help='Protocol number')
latest_protocol_contents_input.add_argument(
    'id', type=str, required=False, help='Unique PD ID of the document')
latest_protocol_contents_input.add_argument(
    'approvalDate', type=str, required=False, help='Approval date of the document in YYYYMMDD format')
latest_protocol_contents_input.add_argument(
    'versionNumber', type=str, required=False, help='Version Number')
latest_protocol_contents_input.add_argument(
    'documentStatus', type=str, required=False, help='Document status, default is "final"')
latest_protocol_contents_input.add_argument(
    'sourceSystem', type=str, required=False, help='Source system calling this API')

# Protocol versions (sorted)
latest_protocol_input = reqparse.RequestParser()
latest_protocol_input.add_argument(
    'protocolNumber', type=str, required=True, help='Protocol number')
latest_protocol_input.add_argument(
    'versionNumber', type=str, required=False, help='Version Number')
latest_protocol_input.add_argument(
    'documentStatus', type=str, required=False, help='Document status, default is "final"')
latest_protocol_input.add_argument(
    'qcStatus', type=str, required=False, help='Quality check validation status, default is "qc_only"')
latest_protocol_input.add_argument(
    'sourceSystem', type=str, required=False, help='Source system calling this API')

latest_protocol_contract_fields = ('protocol', 'versionNumber', 'sponsor', 'documentStatus', 'aidocId', 'allVersions', 'approvalDate',
                                   'draftNumber', 'uploadDate', 'projectId', 'amendmentNumber', 'amendmentFlag', 'protocolShortTitle', 'protocolTitle', 'indications', 'trialPhase', 'blinded')

latest_protocol_get = api.model('Document Processing Status Model',
                                {
                                    'protocol': fields.String(readOnly=True,
                                                              description='Protocol Number of the latest protocol'),
                                    'versionNumber': fields.String(readOnly=True,
                                                                   description='Latest Version Number of the protocol'),
                                    'sponsor': fields.String(readOnly=True,
                                                             description='Sponsor name of the latest protocol'),
                                    'documentStatus': fields.String(readOnly=True,
                                                                    description='Status(draft/final) of latest protocol'),
                                    'id': fields.String(readOnly=True,
                                                             description='Unique PD ID of the latest protocol'),
                                    'allVersions': fields.String(readOnly=True,
                                                                 description='All the available version details'),
                                    'approvalDate': fields.String(readOnly=True, description='Approval date (in YYYYMMDD format) of the latest protocol'),
                                    'draftNumber': fields.String(readOnly=True, description='Draft number of the latest protocol'),
                                    'uploadDate': fields.String(readOnly=True, description='Upload date in ISO-8601 format'),
                                    'projectId': fields.String(readOnly=True, description='projectId of the latest protocol'),
                                    'amendmentNumber': fields.String(readOnly=True, description='Amendment number of the latest protocol'),
                                    'amendmentFlag': fields.String(readOnly=True, description='Amendment flag(Y/N) of the latest protocol'),
                                    'shortTitle': fields.String(readOnly=True, description='Protocol Short title of the latest protocol'),
                                    'protocolTitle': fields.String(readOnly=True, description='Protocol title of the latest protocol'),
                                    'indication': fields.String(readOnly=True, description='Multiple indications of the latest protocol'),
                                    'trialPhase': fields.String(readOnly=True, description='Trial phase of the latest protocol'),
                                    'blinded': fields.String(readOnly=True, description='Blind strategy of the latest protocol'),
                                }
                                )

# Protocol attributes and SOA
protocol_attr_soa_input = reqparse.RequestParser()
protocol_attr_soa_input.add_argument(
    'protocolNumber', type=str, required=True, help='Protocol number')
protocol_attr_soa_input.add_argument(
    'id', type=str, required=True, help='Unique PD id of protocol')
protocol_attr_soa_input.add_argument(
    'sourceSystem', type=str, required=False, help='Source system calling this API')

protocol_attr_soa_get = api.model('Protocol Attributes and Normalized SOA',
                                  {
                                      'id': fields.String(readOnly=True,
                                                          description='Unique id of the protocol'),
                                      'protocolAttributes': fields.String(readOnly=True,
                                                                          description='Attributes of protocol'),
                                      'normalizedSOA': fields.String(readOnly=True,
                                                                     description='Normalized SOA')
                                  })

# Normalized SOA compare
norm_soa_compare_input = reqparse.RequestParser()
norm_soa_compare_input.add_argument(
    'protocolNumber', type=str, required=True, help='Protocol number')
norm_soa_compare_input.add_argument(
    'baseDocId', type=str, required=True, help='Unique PD id of protocol')
norm_soa_compare_input.add_argument(
    'compareDocId', type=str, required=True, help='compare PD id of protocol')
norm_soa_compare_input.add_argument(
    'sourceSystem', type=str, required=False, help='Source system calling this API')

norm_soa_compare_get = api.model('Normalized SOA compare',
                                 {
                                     'normalizedSOADifference': fields.String(readOnly=True,
                                                                              description='Normalized SOA Difference')
                                 })

pd_qc_check_update_post = reqparse.RequestParser()
pd_qc_check_update_post.add_argument('aidoc_id',
                                     type=str,
                                     required=True,
                                     help='Aidoc id'),
pd_qc_check_update_post.add_argument('parent_path',
                                     type=str,
                                     required=True,
                                     help='DFS parent location')
pd_qc_check_update_post.add_argument('qcApprovedBy',
                                     type=str,
                                     required=True,
                                     help='Qc_approved_by')


eTMFA_object_post = reqparse.RequestParser()
eTMFA_object_post.add_argument('sourceFileName',
                               type=str,
                               required=True,
                               help='Source Input document name')
eTMFA_object_post.add_argument('versionNumber',
                               type=str,
                               required=True,
                               help='Version Number')
eTMFA_object_post.add_argument('protocolNumber',
                               type=str,
                               required=False,
                               help='Protocol number')
eTMFA_object_post.add_argument('sponsor',
                               type=str,
                               required=True,
                               help='Sponsor')
eTMFA_object_post.add_argument('sourceSystem',
                               type=str,
                               required=False,
                               help='Source system')
eTMFA_object_post.add_argument('documentStatus',
                               type=str,
                               required=True,
                               choices=[
                                   doc_class.value for doc_class in DocumentClass],
                               help='Document Status(Draft/Final)')
eTMFA_object_post.add_argument('studyStatus',
                               type=str,
                               required=False,
                               help='Study Status')
eTMFA_object_post.add_argument('amendmentNumber',
                               type=str,
                               required=True,
                               choices=['Y', 'N'],
                               help='Amendment Number')
eTMFA_object_post.add_argument('projectID',
                               type=str,
                               required=False,
                               help='project ID')
eTMFA_object_post.add_argument('environment',
                               type=str,
                               required=False,
                               help='Environment')
eTMFA_object_post.add_argument('indication',
                               type=str,
                               required=True,
                               help='Indication')
eTMFA_object_post.add_argument('moleculeDevice',
                               type=str,
                               required=True,
                               help='Molecule Device')
eTMFA_object_post.add_argument('userId',
                               type=str,
                               required=True,
                               help='userId')
eTMFA_object_post.add_argument('file',
                               type=werkzeug.datastructures.FileStorage,
                               location='files',
                               required=True,
                               help='Input document')
eTMFA_object_post.add_argument('workFlowName',
                               type=str,
                               required=False,
                               help='Workflow name')
eTMFA_object_post.add_argument('duplicateCheck',
                               type=inputs.boolean,
                               required=False,
                               help='duplicate check enable disable')


wf_object_post = reqparse.RequestParser()
wf_object_post.add_argument('docId',
                               type=str,
                               required=True,
                               help='flow id')
wf_object_post.add_argument('workFlowName',
                               type=str,
                               required=True,
                               help='Workflow name')
wf_object_post.add_argument('docIdToCompare',
                               type=str,
                               required=False,
                               help='doc id to compare')
                               

document_processing_object_put = api.model('Document feedback definition',
                                           {
                                               'id': fields.String(required=True,
                                                                   description='The unique identifier (UUID) of a document processing job.'),
                                               'feedbackSource': fields.String(required=True,
                                                                               description='Feedback source for the processed document'),
                                               'userId': fields.String(required=False, description='userId'),
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

latest_protocol_input_by_date_range = reqparse.RequestParser()
latest_protocol_input_by_date_range.add_argument(
    'documentStatus', type=str, required=False, help='Document status, default is "final"')
latest_protocol_input_by_date_range.add_argument(
    'qcStatus', type=str, required=False, help='Quality check validation status, default is "qc_only"')
latest_protocol_input_by_date_range.add_argument(
    'approvalDate', type=str, required=False, help='approval date in YYYYMMDD format')
latest_protocol_input_by_date_range.add_argument(
    'uploadDate', type=str, required=False, help='Upload date in YYYYMMDD format')
latest_protocol_input_by_date_range.add_argument(
    'versionDate', type=str, required=False, help='version date in YYYYMMDD format')
latest_protocol_input_by_date_range.add_argument(
    'startDate', type=str, required=False, help='start date in YYYYMMDD format')
latest_protocol_input_by_date_range.add_argument(
    'endDate', type=str, required=False, help='end date in YYYYMMDD format')

latest_protocol_get_by_date_range = api.model('Document Processing Status Model',
                                              {
                                                  'protocol': fields.String(readOnly=True,
                                                                            description='Protocol Number of the latest protocol'),
                                                  'versionNumber': fields.String(readOnly=True,
                                                                                 description='Latest Version Number of the protocol'),
                                                  'sponsor': fields.String(readOnly=True,
                                                                           description='Sponsor name of the latest protocol'),
                                                  'documentStatus': fields.String(readOnly=True,
                                                                                  description='Status(draft/final) of latest protocol'),
                                                  'qcStatus': fields.String(readOnly=True,
                                                                                  description='Status(QC, QC_COMPLETED) of latest protocol'),
                                                  'id': fields.String(readOnly=True,
                                                                           description='Unique PD ID of the latest protocol'),
                                                  'allVersions': fields.String(readOnly=True,
                                                                               description='All the available version details'),
                                                  'versionDate': fields.String(readOnly=True, description='version date inin YYYYMMDD format'),
                                                  'approvalDate': fields.String(readOnly=True, description='Approval date (in YYYYMMDD format) of the latest protocol'),
                                                  'draftNumber': fields.String(readOnly=True, description='Draft number of the latest protocol'),
                                                  'uploadDate': fields.String(readOnly=True, description='Upload date in ISO-8601 format'),
                                                  'projectId': fields.String(readOnly=True, description='projectId of the latest protocol'),
                                                  'amendmentNumber': fields.String(readOnly=True, description='Amendment number of the latest protocol'),
                                                  'amendmentFlag': fields.String(readOnly=True, description='Amendment flag(Y/N) of the latest protocol'),
                                                  'shortTitle': fields.String(readOnly=True, description='Protocol Short title of the latest protocol'),
                                                  'protocolTitle': fields.String(readOnly=True, description='Protocol title of the latest protocol'),
                                                  'indication': fields.String(readOnly=True, description='Multiple indications of the latest protocol'),
                                                  'trialPhase': fields.String(readOnly=True, description='Trial phase of the latest protocol'),
                                                  'blinded': fields.String(readOnly=True, description='Blind strategy of the latest protocol'),
                                              }
                                              )
#added for pd 2.0
# Protocol normalized SOA
protocol_soa_input = reqparse.RequestParser()
protocol_soa_input.add_argument('protocolNumber', type=str, required=True, help='Protocol number')
protocol_soa_input.add_argument('id', type=str, required=True, help='Unique PD id of protocol')
protocol_soa_input.add_argument('sourceSystem', type=str, required=False, help='Source system calling this API')

protocol_soa_get = api.model('Protocol Normalized SOA',
                             {
                                 'id': fields.String(readOnly=True,
                                                     description='Unique id of the protocol'),
                                 
                                 'normalizedSOA': fields.String(readOnly=True,
                                                                  description='Normalized SOA')
                             })

# for metadata get
metadata_summary_input = reqparse.RequestParser()
metadata_summary_input.add_argument('op', type=str, required=True, help='Operation required to get metadata(provide "metadata" or "metaparam")')
metadata_summary_input.add_argument('aidocId', type=str, required=True, help='Unique protocol document id')
metadata_summary_input.add_argument('fieldName', type=str, required=False, help='Metadata fieldName')


# for metadata create
metadata_summary_create = reqparse.RequestParser()
metadata_summary_create.add_argument('op', type=str, required=True, help='Operation required to create metadata(provide "addField" or "addAttributes")')
metadata_summary_create.add_argument('aidocId', type=str, required=True, help='Unique protocol document id')
metadata_summary_create.add_argument('fieldName', type=str, required=True, help='Metadata fieldName')
metadata_summary_create.add_argument('attributes', type=dict,action='append', required=False, help='Metadata attributes')
metadata_summary_add = api.model('API for external systems and BPO view to create metadata attributes',
                             {
                                 'isAdded': fields.Boolean(readOnly=True,
                                                     description='check metadata added or not'),
                                 'isDuplicate': fields.Boolean(readOnly=True,
                                                     description='check metadata duplicate or not'),
                                 'error' : fields.String(readOnly=True,
                                                     description='error message')
                                 
                             })


# for metadata update
metadata_summary = reqparse.RequestParser()
metadata_summary.add_argument('aidocId', type=str, required=True, help='Unique protocol document id')
metadata_summary.add_argument('fieldName', type=str, required=True, help='Metadata fieldName')
metadata_summary.add_argument('attributes', type=dict,action='append', required=True, help='Metadata attributes')
metadata_summary_update = api.model('API for external systems and BPO view to update metadata attributes',
                             {
                                 'isAdded': fields.Boolean(readOnly=True,
                                                     description='check metadata added or not'),
                                 'isDuplicate': fields.Boolean(readOnly=True,
                                                     description='check metadata duplicate or not'),
                                 'error' : fields.String(readOnly=True,
                                                     description='error message')
                                 
                             })


# for metadata delete
metadata_detele_summary = reqparse.RequestParser()
metadata_detele_summary.add_argument('op', type=str, required=True, help='Operation required to delete metadata(provide "deleteField" or "deleteAttribute")')
metadata_detele_summary.add_argument('aidocId', type=str, required=True, help='Unique protocol document id')
metadata_detele_summary.add_argument('fieldName', type=str, required=True, help='Metadata fieldName')
metadata_detele_summary.add_argument('attributeNames', type=str,action='append', required=False, help='Metadata attributes')

metadata_summary_delete = api.model('API for external systems and BPO view to delete metadata attributes',
                             {
                                 'isDeleted': fields.Boolean(readOnly=True,
                                                     description='check metadata deleted or not'),
                                 'error' : fields.String(readOnly=True,
                                                     description='error message')
                                 
                             })
