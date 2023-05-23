import werkzeug
from flask_restplus import fields, reqparse, inputs
from etmfa.server.api import api
from etmfa.workflow.messaging.models.document_class import DocumentClass

PROTOCOL_UNIQUE_ID = 'Unique PD id of protocol'
PROTOCOL_NUMBER = 'Protocol number'
METADATA_ATTRIBUTES = 'Metadata attributes'
METADATA_FIELDNAME = 'Metadata fieldName'
ETMFA_UNIQUE_ID = 'The unique identifier (UUID) of eTMFA document.'
VERSION_NUMBER = 'Version Number'
DOCUMENT_STATUS = 'Document status, default is "final"'
ERROR_MESSAGE = 'error message'
UNIQUE_PROTOCOL_DOCUMENT_ID = 'Unique protocol document id'
SOURCE_SYSYTEM = 'Source system calling this API'
DOCUMENT_PROCESSING_MODEL = 'Document Processing Status Model'
SOURCE_INPUT_DOCUMENT = 'Source Input document name'
METADATA_ATTRIBUTE_IDS = 'metadata attribute Ids'
UNIQUE_IDENTIFIER_PROCESSING_JOB='The unique identifier (UUID) of a document processing job'
DOC_ID='doc id'
LINK_LVL_1_6='Link level in between 1 to 6'
USER_ID='user id'
DOC_SECTION_ID='doc section id'

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

eTMFA_object_get = api.model(DOCUMENT_PROCESSING_MODEL,
                             {
                                 'id': fields.String(readOnly=True,
                                                     description=ETMFA_UNIQUE_ID),
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

PD_qc_get = api.model(DOCUMENT_PROCESSING_MODEL,
                      {
                          'aidocid': fields.String(readOnly=True,
                                                   description='The aidocid for QC update.'),
                          'qcApprovedBy': fields.String(readOnly=True,
                                                        description='The approved by user id.'),

                      }
                      )

eTMFA_object_get_status = api.model(DOCUMENT_PROCESSING_MODEL,
                                    {
                                        'id': fields.String(readOnly=True,
                                                            description=ETMFA_UNIQUE_ID),
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
                                                      description=ETMFA_UNIQUE_ID),
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
                                    help=SOURCE_INPUT_DOCUMENT)
eTMFA_attributes_input.add_argument('protocolNumber',
                                    type=str,
                                    required=True,
                                    help=PROTOCOL_NUMBER)
eTMFA_attributes_input.add_argument('projectId',
                                    type=str,
                                    required=True,
                                    help='Project ID')
eTMFA_attributes_input.add_argument('versionNumber',
                                    type=str,
                                    required=False,
                                    help=VERSION_NUMBER)
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
                                    help=USER_ID)
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
    'protocolNumber', type=str, required=True, help=PROTOCOL_NUMBER)
latest_protocol_download_input.add_argument(
    'id', type=str, required=False, help='Unique PD ID of the document')
latest_protocol_download_input.add_argument(
    'approvalDate', type=str, required=False, help='Approval date of the document in YYYYMMDD format')
latest_protocol_download_input.add_argument(
    'versionNumber', type=str, required=False, help=VERSION_NUMBER)
latest_protocol_download_input.add_argument(
    'documentStatus', type=str, required=False, help=DOCUMENT_STATUS)
latest_protocol_download_input.add_argument(
    'sourceSystem', type=str, required=False, help=SOURCE_SYSYTEM)

# Latest protocol contents
latest_protocol_contents_input = reqparse.RequestParser()
latest_protocol_contents_input.add_argument(
    'protocolNumber', type=str, required=True, help=PROTOCOL_NUMBER)
latest_protocol_contents_input.add_argument(
    'id', type=str, required=False, help='Unique PD ID of the document')
latest_protocol_contents_input.add_argument(
    'approvalDate', type=str, required=False, help='Approval date of the document in YYYYMMDD format')
latest_protocol_contents_input.add_argument(
    'versionNumber', type=str, required=False, help=VERSION_NUMBER)
latest_protocol_contents_input.add_argument(
    'documentStatus', type=str, required=False, help=DOCUMENT_STATUS)
latest_protocol_contents_input.add_argument(
    'sourceSystem', type=str, required=False, help=SOURCE_SYSYTEM)

# Protocol versions (sorted)
latest_protocol_input = reqparse.RequestParser()
latest_protocol_input.add_argument(
    'protocolNumber', type=str, required=True, help=PROTOCOL_NUMBER)
latest_protocol_input.add_argument(
    'versionNumber', type=str, required=False, help=VERSION_NUMBER)
latest_protocol_input.add_argument(
    'documentStatus', type=str, required=False, help=DOCUMENT_STATUS)
latest_protocol_input.add_argument(
    'qcStatus', type=str, required=False, help='Quality check validation status, default is "qc_only"')
latest_protocol_input.add_argument(
    'sourceSystem', type=str, required=False, help=SOURCE_SYSYTEM)

latest_protocol_contract_fields = (
    'protocol', 'versionNumber', 'sponsor', 'documentStatus', 'id', 'allVersions', 'approvalDate',
    'draftNumber', 'draftVersion', 'uploadDate', 'projectId', 'amendmentNumber', 'amendmentFlag', 'shortTitle', 'protocolTitle',
    'indication', 'phase', 'blinded')

latest_protocol_get = api.model(DOCUMENT_PROCESSING_MODEL,
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
                                    'approvalDate': fields.String(readOnly=True,
                                                                  description='Approval date (in YYYYMMDD format) of the latest protocol'),
                                    'draftNumber': fields.String(readOnly=True,
                                                                 description='Draft number of the latest protocol'),
                                    'draftVersion': fields.String(readOnly=True,
                                                                  description='Draft version of the latest protocol'),
                                    'uploadDate': fields.String(readOnly=True,
                                                                description='Upload date in ISO-8601 format'),
                                    'projectId': fields.String(readOnly=True,
                                                               description='projectId of the latest protocol'),
                                    'amendmentNumber': fields.String(readOnly=True,
                                                                     description='Amendment number of the latest protocol'),
                                    'amendmentFlag': fields.String(readOnly=True,
                                                                   description='Amendment flag(Y/N) of the latest protocol'),
                                    'shortTitle': fields.String(readOnly=True,
                                                                description='Protocol Short title of the latest protocol'),
                                    'protocolTitle': fields.String(readOnly=True,
                                                                   description='Protocol title of the latest protocol'),
                                    'indication': fields.String(readOnly=True,
                                                                description='Multiple indications of the latest protocol'),
                                    'phase': fields.String(readOnly=True,
                                                           description='Trial phase of the latest protocol'),
                                    'blinded': fields.String(readOnly=True,
                                                             description='Blind strategy of the latest protocol'),
                                }
                                )

# Protocol attributes and SOA
protocol_attr_soa_input = reqparse.RequestParser()
protocol_attr_soa_input.add_argument(
    'protocolNumber', type=str, required=True, help=PROTOCOL_NUMBER)
protocol_attr_soa_input.add_argument(
    'id', type=str, required=True, help=PROTOCOL_UNIQUE_ID)
protocol_attr_soa_input.add_argument(
    'sourceSystem', type=str, required=False, help=SOURCE_SYSYTEM)

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
    'protocolNumber', type=str, required=True, help=PROTOCOL_NUMBER)
norm_soa_compare_input.add_argument(
    'baseDocId', type=str, required=True, help=PROTOCOL_UNIQUE_ID)
norm_soa_compare_input.add_argument(
    'compareDocId', type=str, required=True, help='compare PD id of protocol')
norm_soa_compare_input.add_argument(
    'sourceSystem', type=str, required=False, help=SOURCE_SYSYTEM)

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
                               help=SOURCE_INPUT_DOCUMENT)
eTMFA_object_post.add_argument('versionNumber',
                               type=str,
                               required=True,
                               help=VERSION_NUMBER)
eTMFA_object_post.add_argument('protocolNumber',
                               type=str,
                               required=False,
                               help=PROTOCOL_NUMBER)
eTMFA_object_post.add_argument('sponsor',
                               type=str,
                               required=False,
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
                               required=False,
                               help='Indication')
eTMFA_object_post.add_argument('moleculeDevice',
                               type=str,
                               required=False,
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
                            required=False,
                            help='Workflow name')
wf_object_post.add_argument('workFlowList', required=False, type=dict, action='append',
                            help='contains json data for list of workflows')
wf_object_post.add_argument('docIdToCompare',
                            type=str,
                            required=False,
                            help='doc id to compare')

document_processing_object_put = api.model('Document feedback definition',
                                           {
                                               'id': fields.String(required=True,
                                                                   description=UNIQUE_IDENTIFIER_PROCESSING_JOB),
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
                                                                       description=UNIQUE_IDENTIFIER_PROCESSING_JOB),
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
    'documentStatus', type=str, required=False, help=DOCUMENT_STATUS)
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

latest_protocol_get_by_date_range = api.model(DOCUMENT_PROCESSING_MODEL,
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
                                                  'versionDate': fields.String(readOnly=True,
                                                                               description='version date inin YYYYMMDD format'),
                                                  'approvalDate': fields.String(readOnly=True,
                                                                                description='Approval date (in YYYYMMDD format) of the latest protocol'),
                                                  'uploadDate': fields.String(readOnly=True,
                                                                              description='Upload date in ISO-8601 format'),
                                                  'projectId': fields.String(readOnly=True,
                                                                             description='projectId of the latest protocol'),
                                                  'amendment': fields.String(readOnly=True,
                                                                                 description='Amendment flag(Y/N) of the latest protocol'),
                                                  'shortTitle': fields.String(readOnly=True,
                                                                              description='Protocol Short title of the latest protocol'),
                                                  'protocolTitle': fields.String(readOnly=True,
                                                                                 description='Protocol title of the latest protocol'),
                                                  'indication': fields.String(readOnly=True,
                                                                              description='Multiple indications of the latest protocol'),
                                                  'phase': fields.String(readOnly=True,
                                                                         description='Trial phase of the latest protocol'),
                                              }
                                              )
# added for pd 2.0
# Protocol normalized SOA
protocol_soa_input = reqparse.RequestParser()
protocol_soa_input.add_argument(
    'id', type=str, required=True, help=PROTOCOL_UNIQUE_ID)
protocol_soa_input.add_argument(
    'sourceSystem', type=str, required=False, help=SOURCE_SYSYTEM)
protocol_soa_input.add_argument(
    'operationValue', type=str, required=False, help='Operation value')
protocol_soa_input.add_argument(
    'footnotes', type=inputs.boolean, required=False, help="Footnotes")

protocol_soa_get = api.model('Protocol Normalized SOA',
                             {
                                 'id': fields.String(readOnly=True,
                                                     description='Unique id of the protocol'),

                                 'normalizedSOA': fields.String(readOnly=True,
                                                                description='Normalized SOA')
                             })

# for normalized soa: update,delete,create operation
protocol_soa_post = reqparse.RequestParser()
protocol_soa_post.add_argument(
    'operation', type=str, required=True, help='Operation to perform')
protocol_soa_post.add_argument(
    'sub_type', type=str, required=True, help='Sub operation to perform')
protocol_soa_post.add_argument(
    'table_props', type=dict, required=False, help=SOURCE_SYSYTEM, action='append')


# for metadata get
metadata_summary_input = reqparse.RequestParser()
metadata_summary_input.add_argument('op', type=str, required=True,
                                    help='Operation required to get metadata(provide "metadata" or "metaparam")')
metadata_summary_input.add_argument(
    'aidocId', type=str, required=False, help=UNIQUE_PROTOCOL_DOCUMENT_ID)
metadata_summary_input.add_argument(
    'fieldName', type=str, required=False, help=METADATA_FIELDNAME)

# for metadata create
metadata_summary_create = reqparse.RequestParser()
metadata_summary_create.add_argument('op', type=str, required=True,
                                     help='Operation required to create metadata(provide "addField" or "addAttributes")')
metadata_summary_create.add_argument(
    'aidocId', type=str, required=False, help=UNIQUE_PROTOCOL_DOCUMENT_ID)
metadata_summary_create.add_argument(
    'fieldName', type=str, required=True, help=METADATA_FIELDNAME)
metadata_summary_create.add_argument(
    'attributes', type=dict, action='append', required=False, help=METADATA_ATTRIBUTES)
metadata_summary_add = api.model('API for external systems and BPO view to create metadata attributes',
                                 {
                                     'isAdded': fields.Boolean(readOnly=True,
                                                               description='check metadata added or not'),
                                     'isDuplicate': fields.Boolean(readOnly=True,
                                                                   description='check metadata duplicate or not'),
                                     'error': fields.String(readOnly=True,
                                                            description=ERROR_MESSAGE)

                                 })

# for metadata update
metadata_summary = reqparse.RequestParser()
metadata_summary.add_argument(
    'aidocId', type=str, required=False, help=UNIQUE_PROTOCOL_DOCUMENT_ID)
metadata_summary.add_argument(
    'fieldName', type=str, required=True, help=METADATA_FIELDNAME)
metadata_summary.add_argument(
    'attributes', type=dict, action='append', required=True, help=METADATA_ATTRIBUTES)
metadata_summary_update = api.model('API for external systems and BPO view to update metadata attributes',
                                    {
                                        'isAdded': fields.Boolean(readOnly=True,
                                                                  description='check metadata added or not'),
                                        'isDuplicate': fields.Boolean(readOnly=True,
                                                                      description='check metadata duplicate or not'),
                                        'error': fields.String(readOnly=True,
                                                               description=ERROR_MESSAGE)

                                    })

# for metadata delete
metadata_detele_summary = reqparse.RequestParser()
metadata_detele_summary.add_argument('op', type=str, required=True,
                                     help='Operation required to delete metadata(provide "deleteField" or "deleteAttribute")')
metadata_detele_summary.add_argument(
    'softDelete', type=bool, required=True, help='True or False value for soft delete')
metadata_detele_summary.add_argument(
    'aidocId', type=str, required=False, help=UNIQUE_PROTOCOL_DOCUMENT_ID)
metadata_detele_summary.add_argument(
    'fieldName', type=str, required=True, help=METADATA_FIELDNAME)
metadata_detele_summary.add_argument('attributeNames', type=str, action='append', required=False,
                                     help=METADATA_ATTRIBUTES)
metadata_detele_summary.add_argument('attributeIds', type=str, action='append', required=False,
                                     help=METADATA_ATTRIBUTE_IDS)

metadata_summary_delete = api.model('API for external systems and BPO view to delete metadata attributes',
                                    {
                                        'isDeleted': fields.Boolean(readOnly=True,
                                                                    description='check metadata deleted or not'),
                                        'error': fields.String(readOnly=True,
                                                               description=ERROR_MESSAGE)

                                    })

# To get section header
section_header_args = reqparse.RequestParser()
section_header_args.add_argument(
    'aidoc_id', type=str, required=True, help=DOC_ID)
section_header_args.add_argument(
    'link_level', type=int, required=True, help=LINK_LVL_1_6)
section_header_args.add_argument(
    'toc', type=int, required=True, help=DOC_SECTION_ID)
section_header_args.add_argument(
    'user_id', type=str, required=False, help=USER_ID)

# to get enriched data
enriched_data_args = reqparse.RequestParser()
enriched_data_args.add_argument(
    'aidoc_id', type=str, required=True, help=DOC_ID)
enriched_data_args.add_argument(
    'link_id', type=str, required=True, help=DOC_SECTION_ID)

# to get section data
section_data_args = reqparse.RequestParser()
section_data_args.add_argument(
    'aidoc_id', type=str, required=True, help=DOC_ID)
section_data_args.add_argument(
    'link_level', type=int, required=False, help=LINK_LVL_1_6)
section_data_args.add_argument(
    'link_id', type=str, required=False, help=DOC_SECTION_ID)
section_data_args.add_argument(
    'user_id', type=str, required=False, help=USER_ID)
section_data_args.add_argument(
    'protocol', type=str, required=False, help='protocol number')

# To get section config data
section_data_config_args = reqparse.RequestParser()
section_data_config_args.add_argument(
    'aidoc_id', type=str, required=True, help=DOC_ID)
section_data_config_args.add_argument(
    'link_level', type=int, required=False, default=1, help=LINK_LVL_1_6)
section_data_config_args.add_argument(
    'toc', type=str, required=False, help='toc 0 or 1 to get section headers')
section_data_config_args.add_argument(
    'link_id', type=str, required=False, default="", help=DOC_SECTION_ID)
section_data_config_args.add_argument('section_text', type=str, required=False,
                                      help='doc section text, table, appendix')
section_data_config_args.add_argument(
    'user_id', type=str, required=False, help=USER_ID)
section_data_config_args.add_argument(
    'protocol', type=str, required=False, help='protocol number')
section_data_config_args.add_argument('config_variables', type=str, required=False,
                                      help='Variables: time_points, clinical_terms, preferred_terms, references, properties, redaction_attributes')

# for dipadata get
dipadata_details_get = reqparse.RequestParser()
dipadata_details_get.add_argument(
    'doc_id', type=str, required=True, help= UNIQUE_PROTOCOL_DOCUMENT_ID)

dipadata_details_input = reqparse.RequestParser()
dipadata_details_input.add_argument('id', type=str, required=False,
                                    help=UNIQUE_IDENTIFIER_PROCESSING_JOB)
dipadata_details_input.add_argument(
    'doc_id', type=str, required=True, help=UNIQUE_PROTOCOL_DOCUMENT_ID)
dipadata_details_input.add_argument(
    'category', type=str, required=False, help='Dipadata Category')

# for Upsert DIPA View Data
dipa_view_data = reqparse.RequestParser()
dipa_view_data.add_argument(
    'id', type=str, required=True, help='unique db id for dipa view data')
dipa_view_data.add_argument(
    'doc_id', type=str, required=False, help='unqiue id of document')
dipa_view_data.add_argument('link_id_1', type=str,
                            required=False, help='link level id 1')
dipa_view_data.add_argument('link_id_2', type=str,
                            required=False, help='link level id 2')
dipa_view_data.add_argument('link_id_3', type=str,
                            required=False, help='link level id 3')
dipa_view_data.add_argument('link_id_4', type=str,
                            required=False, help='link level id 4')
dipa_view_data.add_argument('link_id_5', type=str,
                            required=False, help='link level id 5')
dipa_view_data.add_argument('link_id_6', type=str,
                            required=False, help='link level id 6')
dipa_view_data.add_argument(
    'userId', type=str, required=True, help='id of user updating the Data')
dipa_view_data.add_argument(
    'userName', type=str, required=True, help='id of user updating the Data')
dipa_view_data.add_argument('dipa_data', type=dict,
                            help='contains json data to be stored against dipa data column')


fetch_workflows_by_userId = reqparse.RequestParser()
fetch_workflows_by_userId.add_argument('userId', type=str, required=True,
                                       help='user id for which workflows will be fetched')
fetch_workflows_by_userId.add_argument(
    'limit', type=str, required=True, help='offset value for pagination')
fetch_workflows_by_userId.add_argument(
    'page_num', type=str, required=True, help='offset value for pagination')

# notification args
notification_args = reqparse.RequestParser()
notification_args.add_argument(
    'doc_id', type=str, required=True, help=DOC_ID)
notification_args.add_argument('event', type=str, required=True,
                               help='Event to trigger notifications example QC_COMPLETED')
notification_args.add_argument('user_id', type=str, required=False, default='',
                               help='User id to exclude notification alert and emails')
notification_args.add_argument('send_mail', type=inputs.boolean, default=False, required=False,
                               help="sending mail default false if need to send mail for event true required")
notification_args.add_argument('test_case', type=inputs.boolean, default=False, required=False,
                               help="This flag is used for test case execution time no mail send")


fetch_workflows_by_doc_id = reqparse.RequestParser()
fetch_workflows_by_doc_id.add_argument('doc_id', type=str, required=True,
                                       help='doc_id id for which workflows will be fetched')
fetch_workflows_by_doc_id.add_argument(
    'days', type=str, required=False, help='number of days')
fetch_workflows_by_doc_id.add_argument('wf_num', type=str, required=False,
                                       help='number of workflows to be fetched')

# fetch confidence Score
fetch_confidence_score = reqparse.RequestParser()
fetch_confidence_score.add_argument('doc_id', type=str, required=False,
                                    help='doc_id id for which workflows will be fetched')
fetch_confidence_score.add_argument('sponsorName', type=str, required=True,
                                    help='Name of the sponsor')
fetch_confidence_score.add_argument('docStatus', type=str, required=False,
                                    help='doc status of protocol metadata table')
