import logging
import uuid
from pathlib import Path
from etmfa.messaging.models.queue_names import EtmfaQueues
from dataclasses import asdict
from etmfa.server.config import Config
from flask import send_from_directory,make_response
from pathlib import Path
from http import HTTPStatus

from etmfa.consts import Consts as consts
from etmfa.db import utils
from etmfa.db import (
    pd_fetch_summary_data,
    save_doc_processing,
    get_doc_processing_by_id,
    get_doc_status_processing_by_id,
    get_file_contents_by_id,
    get_latest_protocol,
    set_draft_version,
    get_attr_soa_details
)
from etmfa.messaging.messagepublisher import MessagePublisher
from etmfa.messaging.models.triage_request import TriageRequest
from etmfa.server.api import api
from etmfa.server.namespaces.serializers import (
    eTMFA_object_get,
    PD_qc_get,
    eTMFA_object_post,
    latest_protocol_input,
    latest_protocol_get,
    eTMFA_object_get_status,
    latest_protocol_download_input,
    latest_protocol_contents_input,
    pd_qc_check_update_post,
    protocol_attr_soa_input,
    protocol_attr_soa_get
)
from etmfa.auth import authenticate
from flask import current_app, request, abort, g
from flask_restplus import Resource, abort

logger = logging.getLogger(consts.LOGGING_NAME)

INVALID_USER_INPUT = 'Invalid user input(s) received: {}'
DOCUMENT_NOT_FOUND = 'Document resource is not found for the requested input(s): {}'
Compare_feature_notavail = 'Comparison for the given base_id {} and compare_id {} not available'
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
    @api.doc(security='apikey')
    @authenticate    
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
        document_status = args['documentStatus'].lower().strip() if args['documentStatus'] is not None else ' '  # Doc status check
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

@ns.route('/<string:id>/status')
@ns.response(404, 'Document Processing resource not found.')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.marshal_with(eTMFA_object_get_status)
    @ns.response(200, 'Success.')
    @api.doc(security='apikey')
    @authenticate  
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


@ns.route('/pd_qc_check_update')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(pd_qc_check_update_post)
    @ns.marshal_with(PD_qc_get)
    @ns.response(200, 'Success.')
    @api.doc(security='apikey')
    @authenticate
    def post(self):
        """Perform post processing once the document completes QC check"""
        args = pd_qc_check_update_post.parse_args()
        try:
            aidocid = args['aidoc_id'] if args['aidoc_id'] is not None else ' '
            userid = args['qcApprovedBy'] if args['qcApprovedBy'] is not None else ''
            resource = pd_fetch_summary_data(aidocid, userid)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(aidocid))
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/mcra_download_protocols')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(latest_protocol_download_input)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate    
    def get(self):
        """Get the source protocol document"""
        args = latest_protocol_download_input.parse_args()
        try:
            protocol_number = args['protocolNumber'] if args['protocolNumber'] is not None else ' '
            aidoc_id = args['id'] if args['id'] is not None else ''
            approval_date = args['approvalDate'] if args['approvalDate'] is not None else ''
            version_number = args['versionNumber'] if args['versionNumber'] is not None else ''
            document_status = args['documentStatus'] if args['documentStatus'] is not None else ''

            input_valid_flg = utils.validate_inputs(protocol_number=protocol_number)            
            if not input_valid_flg:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(404, INVALID_USER_INPUT.format(args))

            resources = get_latest_protocol(protocol_number=protocol_number, aidoc_id=aidoc_id, version_number=version_number, approval_date=approval_date, document_status=document_status, is_top_1_only=True)
            aligned_resources = utils.post_process_resource(resources, multiple_records=False)

            if aligned_resources is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(args))
            p=Path(aligned_resources['documentFilePath'])
            path=p.name
            DOWNLOAD_DIRECTORY=p.parent
            try:
                response = make_response(send_from_directory(DOWNLOAD_DIRECTORY,path, as_attachment=True))
                return response
            except Exception as e :
                return abort(404, DOCUMENT_NOT_FOUND.format(args))


        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/mcraattributes')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(latest_protocol_contents_input)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate    
    def get(self):
        """Get the digitized file contents"""
        resource = None
        protocol_number_verified = False
        args = latest_protocol_contents_input.parse_args()

        try:
            protocol_number = args['protocolNumber'] if args['protocolNumber'] is not None else ' '
            aidoc_id = args['id'] if args['id'] is not None else ''
            approval_date = args['approvalDate'] if args['approvalDate'] is not None else ''
            version_number = args['versionNumber'] if args['versionNumber'] is not None else ''
            document_status = args['documentStatus'] if args['documentStatus'] is not None else ''

            input_valid_flg = utils.validate_inputs(protocol_number=protocol_number)            
            if not input_valid_flg:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(404, INVALID_USER_INPUT.format(args))

            if not aidoc_id:
                resources = get_latest_protocol(protocol_number=protocol_number, aidoc_id=aidoc_id, version_number=version_number, approval_date=approval_date, document_status=document_status, is_top_1_only=True)
                aligned_resources = utils.post_process_resource(resources, multiple_records=False)
                expected_aidoc_id = '' if aligned_resources is None else aligned_resources['aidocId']
                protocol_number_verified = True
            else:
                expected_aidoc_id = aidoc_id

            if expected_aidoc_id:
                resource = get_file_contents_by_id(protocol_number=protocol_number, aidoc_id=expected_aidoc_id, protocol_number_verified=protocol_number_verified)
            
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))

@ns.route('/protocol_versions')
@ns.route('/mcra_latest_protocol')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(latest_protocol_input)
    @ns.marshal_with(latest_protocol_get)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get all the protocols processed in PD based on input parameters"""
        args = latest_protocol_input.parse_args()
        try:
            cleaned_inputs = utils.clean_inputs(protocol_number = args['protocolNumber'], version_number = args['versionNumber'], \
                document_status = args['documentStatus'], qc_status = args['qcStatus'])
            protocol_number = cleaned_inputs.get('protocol_number', '')
            version_number = cleaned_inputs.get('version_number', '')
            document_status = cleaned_inputs.get('document_status', '')
            qc_status = cleaned_inputs.get('qc_status', '')

            if not protocol_number:
                logger.error(f"Invalid protocol_number received: {args}")
                return abort(404, INVALID_USER_INPUT.format(args))

            resources = get_latest_protocol(protocol_number=protocol_number, version_number=version_number, document_status=document_status, \
                qc_status=qc_status, is_top_1_only=False)
            aligned_resources = utils.post_process_resource(resources, multiple_records=True)

            if aligned_resources is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(args))
            else:
                return aligned_resources
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))

@ns.route('/protocol_attributes_soa')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(protocol_attr_soa_input)
    @ns.marshal_with(protocol_attr_soa_get)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate    
    def get(self):
        """Get Protocol Attributes and Normalized SOA"""
        args = protocol_attr_soa_input.parse_args()
        try:
            cleaned_inputs = utils.clean_inputs(protocol_number = args['protocolNumber'], aidoc_id = args['id'])
            protocol_number = cleaned_inputs.get('protocol_number', '')
            aidoc_id = cleaned_inputs.get('aidoc_id', '')

            if not protocol_number or not aidoc_id:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))

            resource = get_attr_soa_details(protocol_number = protocol_number, aidoc_id = aidoc_id)

            if len(resource) == 0:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))
