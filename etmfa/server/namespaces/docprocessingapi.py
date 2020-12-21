import logging
import requests
import uuid
import os
import json
from pathlib import Path
from etmfa.messaging.models.queue_names import EtmfaQueues
from dataclasses import asdict
from etmfa.server.config import Config

from etmfa.consts import Consts as consts
from etmfa.db import (
    save_doc_processing,
    save_doc_processing_duplicate,
    save_doc_feedback,
    get_doc_resource_by_id,
    get_doc_processing_by_id,
    get_doc_processed_by_id,
    get_doc_processed_by_protocolnumber,
    get_doc_attributes_by_protocolnumber,
    get_doc_proc_metrics_by_id,
    get_doc_status_processing_by_id,
    get_mcra_attributes_by_protocolnumber,
    get_compare_documents,
    get_compare_documents_validation,
    add_compare_event,
    upsert_attributevalue,
    get_compare_documents_by_docid
)
from etmfa.messaging.messagepublisher import MessagePublisher
from etmfa.messaging.models.triage_request import TriageRequest
from etmfa.messaging.models.compare_request import CompareRequest
from etmfa.messaging.models.feedback_request import FeedbackRequest
from etmfa.messaging.models.document_class import DocumentClass
from etmfa.server.api import api
from etmfa.server.namespaces.serializers import (
    metadata_post,
    eTMFA_object_get,
    eTMFA_object_get_status,
    eTMFA_metrics_get,
    eTMFA_attributes_get,
    eTMFA_object_post,
    document_processing_object_put,
    document_processing_object_put_get,
    pd_object_get_summary,
    eTMFA_attributes_input,
    mCRA_attributes_get,
    mCRA_attributes_input,
    pd_compare_object_post,
    pd_compare_get,
    pd_compare_post_response,
    pd_compare_object_input_get,
    pd_compare_by_docid_object_get
)
from flask import current_app, request, abort, g
from flask_restplus import Resource, abort

from etmfa.api_response_handlers import SummaryResponse

logger = logging.getLogger(consts.LOGGING_NAME)
DOCUMENT_NOT_FOUND = 'Document Processing resource not found for given data: {}'
SERVER_ERROR = 'Server error: {}'
DOCUMENT_COMPARISON_ALREADY_PRESENT = 'Comparison already present for given protocols, use get attributes with compare id to get details: {}'

ns = api.namespace('PD', path='/v1/documents', description='REST endpoints for PD workflows.')




@ns.route('/')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(eTMFA_object_post, validate=True)
    @ns.marshal_with(eTMFA_object_get)
    @ns.response(400, 'Invalid Request.')
    @ns.response(200, 'Success')
    def post(self):
        """Create document Processing REST object and returns document Processing API object """

        args = eTMFA_object_post.parse_args()

        # Generate ID
        _id = uuid.uuid4()
        _id = str(_id)
        g.aidocid = _id
        logger.info("Document received for Processing from: {}".format(request.remote_addr))

        # get save path and output path
        processing_dir = Path(Config.DFS_UPLOAD_FOLDER).joinpath(_id)
        processing_dir.mkdir(exist_ok=True, parents=True)
        file = args['file']
        filename_main = file.filename

        # build file path in the processing directory
        file_path = processing_dir.joinpath(filename_main)
        # Save document in the processing directory
        file.save(str(file_path))
        logger.info("Document saved at location: {}".format(file_path))

        source_filename = args['sourceFileName'] if args['sourceFileName'] is not None else ' '
        version_number = args['versionNumber'] if args['versionNumber'] is not None else ' '
        protocol = args['protocolNumber'] if args['protocolNumber'] is not None else ' '  # protocol check
        document_status = args['documentStatus'] if args['documentStatus'] is not None else ' '  # Doc status check
        environment = args['environment'] if args['environment'] is not None else ' '
        source_system = args['sourceSystem'] if args['sourceSystem'] is not None else ' '
        sponsor = args['sponsor'] if args['sponsor'] is not None else ' '
        study_status = args['studyStatus'] if args['studyStatus'] is not None else ' '  # Study status check
        amendment_number = args['amendmentNumber'] if args['amendmentNumber'] is not None else ' '
        project_id = args['projectID'] if args['projectID'] is not None else ' '
        indication = args['indication'] if args['indication'] is not None else ' '
        molecule_device = args['moleculeDevice'] if args['moleculeDevice'] is not None else ' '
        user_id = args['userId'] if args['userId'] is not None else ' '

        save_doc_processing(args, _id, str(file_path))
        # duplicatecheck = save_doc_processing_duplicate(args, _id, filename_main, str(file_path))#this will be taken out if duplicate check is not requested
        parameters = {
                        "sponser": sponsor,
                        "protocol": protocol,
                        "VersionNumber": version_number,
                        "Amendment": amendment_number
                    }
        #TODO- Make API URL configurable based on environment
        response = requests.get("http://ca2spdml01q:8000/api/duplicate_check/", params=parameters)
        if response.json():
            return response.json()
        else:
            BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
            EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']
            print("reached triage request sent")
            post_req_msg = TriageRequest(_id, str(file_path), source_filename, version_number, protocol, document_status,
                                        environment, source_system, sponsor, study_status, amendment_number, project_id,
                                        indication, molecule_device, user_id)

            MessagePublisher(BROKER_ADDR, EXCHANGE).send_dict(asdict(post_req_msg), EtmfaQueues.TRIAGE.request)

            # Return response object
            return get_doc_processing_by_id(_id, full_mapping=True)


@ns.route('/<string:id>/feedback')
@ns.response(200, 'Success.')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(document_processing_object_put)
    @ns.marshal_with(document_processing_object_put_get)
    def put(self, id):
        """Feedback attributes to document processed"""

        # format data for finalisation service to update IQVDocument

        g.aidocid = id
        feedbackdata = request.json
        id_fb = feedbackdata['id']
        feedback_source = feedbackdata['feedbackSource']
        customer = feedbackdata['customer']
        protocol = feedbackdata['protocol']
        country = feedbackdata['country']
        site = feedbackdata['site']
        document_class = feedbackdata['documentClass']
        document_date = feedbackdata['documentDate']
        document_classification = feedbackdata['documentClassification']
        name = feedbackdata['name']
        user_id = feedbackdata['userId']
        language = feedbackdata['language']
        document_rejected = feedbackdata['documentRejected']
        attribute_auxillary_list = feedbackdata['attributeAuxillaryList']

        resourcefound = get_doc_resource_by_id(id)
        if resourcefound is None:
            return abort(404, DOCUMENT_NOT_FOUND.format(id))

        saved_resource = save_doc_feedback(id, feedbackdata)

        # Send async FormattingDeconstructionRequest
        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']

        # Send FeedbackRequest
        feedback_req_msg = FeedbackRequest(
            id_fb,
            resourcefound.documentFilePath,
            feedback_source,
            customer,
            protocol,
            country,
            site,
            document_class,
            document_date,
            document_classification,
            name,
            language,
            document_rejected,
            attribute_auxillary_list,
            user_id
        )
        MessagePublisher(BROKER_ADDR, EXCHANGE).send_dict(asdict(feedback_req_msg), EtmfaQueues.FEEDBACK.request)

        return saved_resource



@ns.route('/<string:id>/key/value')
@ns.response(404, 'Document Processing resource not found.')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(metadata_post)
    @ns.marshal_with(eTMFA_attributes_get)
    @ns.response(200, 'Success.')
    def patch(self, id):
        """Update document attributes with key value """
        g.aidocid = id
        resource = get_doc_status_processing_by_id(id, full_mapping=True)
        if resource is None:
            return abort(404, DOCUMENT_NOT_FOUND.format(id))
        else:
            md = request.json
            for m in md['metadata']:
                upsert_attributevalue(id, m['name'], m['val'])
            return get_doc_processed_by_id(id)



@ns.route('/<string:id>/status')
@ns.response(404, 'Document Processing resource not found.')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.marshal_with(eTMFA_object_get_status)
    @ns.response(200, 'Success.')
    def get(self, id):
        """Get document processing object status. This includes any locations of processed documents"""
        try:
            g.aidocid = id
            resource = get_doc_status_processing_by_id(id, full_mapping=True)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(id))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/<string:id>/metrics')
@ns.response(200, 'Success.')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.marshal_with(eTMFA_metrics_get)
    def get(self, id):
        """Returns metrics of document processed"""
        try:
            g.aidocid = id
            resource = get_doc_proc_metrics_by_id(id, full_mapping=True)
            if resource is None:
                return abort(404, 'Document Processing resource not found id: {}'.format(id))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/attributes')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(eTMFA_attributes_input)
    @ns.marshal_with(eTMFA_attributes_get)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    def get(self):
        """Get the document processing object attributes"""
        args = eTMFA_attributes_input.parse_args()
        try:
            id = args['docId'] if args['docId'] is not None else ' '
            protocol_number = args['protocolNumber'] if args['protocolNumber'] is not None else ' '
            project_id = args['projectId'] if args['projectId'] is not None else ' '
            doc_status = args['docStatus'] if args['docStatus'] is not None else ' '
            resource = get_doc_attributes_by_protocolnumber(id, protocol_number, project_id, doc_status)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(protocol_number))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/mcraattributes')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(mCRA_attributes_input)
    @ns.marshal_with(mCRA_attributes_get)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    def get(self):
        """Get the document processing object attributes"""
        args = mCRA_attributes_input.parse_args()
        try:
            protocol_number = args['protocolNumber'] if args['protocolNumber'] is not None else ' '
            resource = get_mcra_attributes_by_protocolnumber(protocol_number)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(protocol_number))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/comparerequest')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(pd_compare_object_post)
    @ns.marshal_with(pd_compare_post_response)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    def post(self):
        """Get the document processing object attributes"""
        _id = uuid.uuid4()
        _id = str(_id)
        compareid = _id
        filedirectory = Config.DFS_UPLOAD_FOLDER
        args = pd_compare_object_post.parse_args()
        try:
            protocol_number = args['protocolNumber'] if args['protocolNumber'] is not None else ' '
            project_id = args['projectId'] if args['projectId'] is not None else ' '
            document_id = args['docId'] if args['docId'] is not None else ' '
            protocol_number2 = args['protocolNumber2'] if args['protocolNumber2'] is not None else ' '
            project_id2 = args['projectId2'] if args['projectId2'] is not None else ' '
            document_id2 = args['docId2'] if args['docId2'] is not None else ' '
            request_type = args['requestType'] if args['requestType'] is not None else ' '
            user_id = args['userId'] if args ['userId'] is not None else ' '
            #check to see if compare already present for given doc id's
            resource = get_compare_documents_validation(protocol_number, project_id, document_id, protocol_number2, project_id2,
                                             document_id2, request_type)
            if resource is None:
                docid = document_id
                docid2 = document_id2
                lookupdir = os.path.join(filedirectory, docid)
                lookupdir2 = os.path.join(filedirectory, docid2)
                file1 = [os.path.join(lookupdir, f) for f in os.listdir(lookupdir) if f.startswith("FIN_")]
                file2 = [os.path.join(lookupdir2, f) for f in os.listdir(lookupdir2) if f.startswith("FIN_")]
                compare_req_msg = {"COMPARE_ID": compareid, "BASE_DOC_ID" : docid, "COMPARE_DOC_ID" : docid2, "BASE_IQVXML_PATH" : file1[0], "COMPARE_IQVXML_PATH" : file2[0], "REQUEST_TYPE" : "COMPARE_TOC"}
                BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
                EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']
                MessagePublisher(BROKER_ADDR, EXCHANGE).send_dict(compare_req_msg, EtmfaQueues.COMPARE.request)
                compare_add = add_compare_event(compare_req_msg, protocol_number, project_id, protocol_number2, project_id2, user_id)
                return compare_add
            else:
                return abort(404, DOCUMENT_COMPARISON_ALREADY_PRESENT.format(protocol_number))
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/compareattributes')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(pd_compare_object_input_get)
    # @ns.marshal_with(pd_compare_get)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    def get(self):
        """Get the document processing object attributes"""
        args = pd_compare_object_input_get.parse_args()
        try:
            compare_id = args['compareid'] if args['compareid'] is not None else ' '
            #check to see if compare already present for given doc id's
            resource = get_compare_documents(compare_id)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(compare_id))
            else:
                return json.dumps(resource)
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/comparedocuments')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(pd_compare_by_docid_object_get)
    # @ns.marshal_with(pd_compare_get)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    def get(self):
        """Get the document processing object attributes"""
        args = pd_compare_by_docid_object_get.parse_args()
        try:
            document_id1 = args['docId1'] if args['docId1'] is not None else ' '
            document_id2 = args['docId2'] if args['docId2'] is not None else ' '
            #retrieve documets for given doc id's
            resource = get_compare_documents_by_docid(document_id1, document_id2)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(document_id1))
            else:
                return json.dumps(resource)
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/<string:id>/summary_section')
@ns.response(404, 'Document Processing resource not found.')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.marshal_with(pd_object_get_summary)
    @ns.response(200, 'Success.')
    def get(self, id):
        """Get summary section details from digitized documents"""
        try:
            g.aidocid = id
            summary_response = SummaryResponse(id)
            summary_dict, _ = summary_response.get_summary_api_response()

            if summary_dict is None:
                return abort(404, f"Summary section not found for [{id}]")
            else:
                return summary_dict
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))
