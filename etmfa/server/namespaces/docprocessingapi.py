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
    get_doc_resource_by_id,
    get_doc_processing_by_id,
    get_doc_processed_by_id,
    get_doc_status_processing_by_id,
    get_mcra_attributes_by_protocolnumber,
    get_compare_documents,
    get_compare_documents_validation,
    add_compare_event,
    upsert_attributevalue,
    set_draft_version
)
from etmfa.messaging.messagepublisher import MessagePublisher
from etmfa.messaging.models.triage_request import TriageRequest
from etmfa.messaging.models.compare_request import CompareRequest
from etmfa.messaging.models.document_class import DocumentClass
from etmfa.server.api import api
from etmfa.server.namespaces.serializers import (
    metadata_post,
    eTMFA_object_get,
    eTMFA_object_get_status,
    eTMFA_attributes_get,
    eTMFA_object_post,
    pd_object_get_summary,
    mCRA_attributes_input,
    pd_compare_object_post,
    pd_compare_get,
    pd_compare_post_response,
    pd_compare_object_input_get
)
from flask import current_app, request, abort, g
from flask_restplus import Resource, abort

logger = logging.getLogger(consts.LOGGING_NAME)
DOCUMENT_NOT_FOUND = 'Document Processing resource not found for given data: {}'
SERVER_ERROR = 'Server error: {}'
DOCUMENT_COMPARISON_ALREADY_PRESENT = 'Comparison already present for given protocols'

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
        version_number = args['versionNumber'] if args['versionNumber'] is not None else ''
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

        draftVersion = set_draft_version(document_status, sponsor, protocol, version_number)
        save_doc_processing(args, _id, str(file_path), draftVersion)
        
        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']

        post_req_msg = TriageRequest(_id, str(file_path), source_filename, version_number, protocol, document_status,
                                    environment, source_system, sponsor, study_status, amendment_number, project_id,
                                    indication, molecule_device, user_id)

        MessagePublisher(BROKER_ADDR, EXCHANGE).send_dict(asdict(post_req_msg), EtmfaQueues.TRIAGE.request)

        # Return response object
        return get_doc_processing_by_id(_id, full_mapping=True)


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


@ns.route('/mcraattributes')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(mCRA_attributes_input)
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
            document_id = args['id1'] if args['id1'] is not None else ' '
            protocol_number2 = args['protocolNumber2'] if args['protocolNumber2'] is not None else ' '
            project_id2 = args['projectId2'] if args['projectId2'] is not None else ' '
            document_id2 = args['id2'] if args['id2'] is not None else ' '
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
            compare_id = args['compareId'] if args['compareId'] is not None else ' '
            #check to see if compare already present for given doc id's
            resource = get_compare_documents(compare_id)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(compare_id))
            else:
                return json.dumps(resource)
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))

