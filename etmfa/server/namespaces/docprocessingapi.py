import logging
import uuid
import hashlib
from etmfa.workflow import WorkFlowParamMissing
from dataclasses import asdict
from etmfa.server.config import Config
from flask import send_from_directory, make_response
from http import HTTPStatus
from pathlib import Path
import json

from flask import request, g
from flask_restplus import Resource, abort

from etmfa.auth import authenticate
from etmfa.consts import Consts as consts
from etmfa.db import feedback_utils as fb_utlis
from etmfa.db import (
    pd_fetch_summary_data,
    get_work_flow_status_by_id,
    get_details_by_elm,
    check_if_document_processed,
    create_doc_Processing_status,
    save_doc_processing,
    get_file_contents_by_id,
    get_latest_protocol,
    update_user_protocols,
    get_attr_soa_details,
    get_attr_soa_compare,
    get_normalized_soa_details,
    get_normalized_soa_table,
    get_protocols_by_date_time_range,
    get_metadata_summary,
    add_metadata_summary,
    update_metadata_summary,
    delete_metadata_summary
)
from etmfa.db import utils
from etmfa.workflow.messaging.models.triage_request import TriageRequest
from etmfa.server.api import api
from etmfa.server.namespaces.serializers import (
    eTMFA_object_get,
    PD_qc_get,
    eTMFA_object_post,
    wf_object_post,
    latest_protocol_input,
    latest_protocol_input_by_date_range,
    latest_protocol_get,
    latest_protocol_get_by_date_range,
    eTMFA_object_get_status,
    latest_protocol_download_input,
    latest_protocol_contents_input,
    pd_qc_check_update_post,
    protocol_attr_soa_input,
    protocol_attr_soa_get,
    norm_soa_compare_input,
    norm_soa_compare_get,
    protocol_soa_input,
    metadata_summary_input,
    metadata_summary_create,
    metadata_summary_update,
    metadata_summary_add,
    metadata_summary,
    metadata_detele_summary,
    metadata_summary_delete
)
from etmfa.workflow.default_workflows import DWorkFLows, DEFAULT_WORKFLOWS
from etmfa.workflow import WorkFlowClient
from etmfa.workflow.messaging.models.generic_request import DocumentRequest, CompareRequest
from etmfa.db.models.work_flow_status import WorkFlowStatus


logger = logging.getLogger(consts.LOGGING_NAME)

INVALID_USER_INPUT = 'Invalid user input(s) received: {}'
DOCUMENT_NOT_FOUND = 'Document resource is not found for the requested input(s): {}'
DUPLICATE_DOCUMENT_REQUEST = 'Duplicate document request '
DOCUMENT_MISSING_FROM_METADATA_TABLE = 'Document missing from protocol metadata table'
SERVER_ERROR = 'Server error: {}'
DOCUMENT_COMPARISON_ALREADY_PRESENT = 'Comparison already present for given protocols'

ns = api.namespace('PD', path='/v1/documents',
                   description='REST endpoints for PD workflows.')


def generate_doc_meta_hash(file_path):
    with open(file_path, 'rb') as fp:
        data = fp.read()
        result = hashlib.sha256(data)
        return result.hexdigest()


@ns.route('/run_work_flow')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(eTMFA_object_post, validate=True)
    @ns.expect(wf_object_post, validate=True)
    @ns.marshal_with(eTMFA_object_get)
    @ns.response(400, 'Invalid Request.')
    @ns.response(200, 'Success')
    @api.doc(security='apikey')
    @authenticate
    def post(self):
        """Create document Processing REST object and returns document Processing API object """

        args = wf_object_post.parse_args()
        # Generate ID
        _id = uuid.uuid4()
        _id = str(_id)
        g.aidocid = _id
        logger.debug("Document received for Processing from: {}".format(
            request.remote_addr))
        doc_id = args['docId']
        work_flow_name = args['workFlowName']
        doc_uid, doc_file_path, protocol = None, None, ''
        try:
            fields = get_details_by_elm(
                WorkFlowStatus, WorkFlowStatus.work_flow_id, doc_id)
            # version_number = fields.get('versionNumber')
            doc_file_path = fields['documentFilePath']
            protocol = fields['protocol_name']

        except Exception as e:
            logger.error(
                'requested document is not in workflow status table'+str(doc_id))
            abort(404, DOCUMENT_MISSING_FROM_METADATA_TABLE)
        work_flow_graph = DEFAULT_WORKFLOWS.get(work_flow_name, None)
        if not work_flow_graph or len(work_flow_graph) < 1:
            abort(404, DOCUMENT_MISSING_FROM_METADATA_TABLE)

        start_service_name = work_flow_graph[0].get('service_name', None)
        if not start_service_name:
           abort(404, str(WorkFlowParamMissing(work_flow_name)))
        create_doc_Processing_status(
            _id, doc_uid, work_flow_name, doc_file_path, protocol)
        doc_request = None
        if work_flow_name == DWorkFLows.DOCUMENT_COMPARE.value:
            doc_id1 = args.get('docIdToCompare', None)
            if not doc_id1:
                abort(404, str(Exception("missing compare id in arguments")))
            doc_request = CompareRequest(_id, doc_id, doc_id1)
        else:
            doc_request = DocumentRequest(_id, doc_id)
        if Config.WORK_FLOW_RUNNER:
            wf_client = WorkFlowClient()
            wf_client.send_msg(work_flow_name, _id,
                               doc_id, asdict(doc_request))
        response = get_work_flow_status_by_id(_id)
        response['id'] = response['work_flow_id']
        response['percentComplete'] = response['percent_complete']
        response['workFlowName'] = response['work_flow_name']
        return response


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
        logger.info("Document received for Processing from: {}".format(
            request.remote_addr))
        # hardcode of id

        # get save path and output path
        processing_dir = Path(Config.DFS_UPLOAD_FOLDER).joinpath(_id)
        processing_dir.mkdir(exist_ok=True, parents=True)
        file = args['file']
        filename_main = file.filename

        # build file path in the processing directory
        filepath = processing_dir.joinpath(filename_main)
        # Save document in the processing directory
        file.save(str(filepath))
        logger.info("Document saved at location: {}".format(filepath))

        source_filename = args['sourceFileName'] if args['sourceFileName'] is not None else ' '
        version_number = args['versionNumber'] if args['versionNumber'] is not None else ''
        # protocol check
        protocol = args['protocolNumber'] if args['protocolNumber'] is not None else ' '
        document_status = args['documentStatus'].lower().strip(
        ) if args['documentStatus'] is not None else ' '  # Doc status check
        environment = args['environment'] if args['environment'] is not None else ' '
        source_system = args['sourceSystem'] if args['sourceSystem'] is not None else ' '
        sponsor = args['sponsor'] if args['sponsor'] is not None else ' '
        # Study status check
        study_status = args['studyStatus'] if args['studyStatus'] is not None else ' '
        amendment_number = args['amendmentNumber'] if args['amendmentNumber'] is not None else ' '
        project_id = args['projectID'] if args['projectID'] is not None else ' '
        indication = args['indication'] if args['indication'] is not None else ' '
        molecule_device = args['moleculeDevice'] if args['moleculeDevice'] is not None else ' '
        user_id = args['userId'] if args['userId'] is not None else ' '
        workflow_name = args['workFlowName'] if args['workFlowName'] is not None else DWorkFLows.FULL_FLOW.value
        duplicate_check = args.get('duplicateCheck', False)
        feedback_run_id = 0

        filepath = str(filepath)
        if duplicate_check:
            doc_uid = generate_doc_meta_hash(filepath)
            is_processed,duplicate_docs=check_if_document_processed(doc_uid)
            if is_processed:
                return abort(409,json.dumps({'duplicate_docs':duplicate_docs},default=str))
        else:
            doc_uid = _id

        create_doc_Processing_status(
            _id, doc_uid, workflow_name, filepath, protocol)
        # # Mark the user primary for the protocol
        update_user_protocols(
            user_id=user_id, project_id=project_id, protocol_number=protocol)

        post_req_msg = TriageRequest(_id, filepath, source_filename, version_number, protocol, document_status,
                                     environment, source_system, sponsor, study_status, amendment_number, project_id,
                                     indication, molecule_device, user_id, feedback_run_id)
        if Config.WORK_FLOW_RUNNER:
            wf_client = WorkFlowClient()
            wf_client.send_msg(workflow_name, _id, doc_uid,
                               asdict(post_req_msg))
        save_doc_processing(args, _id, filepath)
        response = get_work_flow_status_by_id(_id)
        response['id'] = response['work_flow_id']
        response['percentComplete'] = response['percent_complete']
        response['workFlowName'] = response['work_flow_name']
        return response


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
            resource = get_work_flow_status_by_id(id)
            if not resource:
                return abort(404, DOCUMENT_NOT_FOUND)
            resource['id'] = resource['work_flow_id']
            resource['percentComplete'] = resource['percent_complete']
            resource['workFlowName'] = resource['work_flow_name']
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
            parent_path = args['parent_path'] if args['parent_path'] is not None else ''

            resource = pd_fetch_summary_data(aidocid, userid)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(aidocid))

            feedback_run_started = fb_utlis.on_qc_approval_complete(
                aidoc_id=aidocid, parent_path=parent_path)
            if not feedback_run_started:
                return abort(404, "Problem in initiating Feedback Run")

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

            input_valid_flg = utils.validate_inputs(
                protocol_number=protocol_number)
            if not input_valid_flg:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(404, INVALID_USER_INPUT.format(args))

            resources = get_latest_protocol(protocol_number=protocol_number, aidoc_id=aidoc_id, version_number=version_number,
                                            approval_date=approval_date, document_status=document_status, is_top_1_only=True)
            aligned_resources = utils.post_process_resource(
                resources, multiple_records=False)

            if aligned_resources is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(args))
            p = Path(aligned_resources['documentFilePath'])
            path = p.name
            DOWNLOAD_DIRECTORY = p.parent
            try:
                response = make_response(send_from_directory(
                    DOWNLOAD_DIRECTORY, path, as_attachment=True))
                return response
            except Exception as e:
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

            input_valid_flg = utils.validate_inputs(
                protocol_number=protocol_number)
            if not input_valid_flg:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(404, INVALID_USER_INPUT.format(args))

            if not aidoc_id:
                resources = get_latest_protocol(protocol_number=protocol_number, aidoc_id=aidoc_id, version_number=version_number,
                                                approval_date=approval_date, document_status=document_status, is_top_1_only=True)
                aligned_resources = utils.post_process_resource(
                    resources, multiple_records=False)
                expected_aidoc_id = '' if aligned_resources is None else aligned_resources[
                    'aidocId']
                protocol_number_verified = True
            else:
                expected_aidoc_id = aidoc_id

            if expected_aidoc_id:
                resource = get_file_contents_by_id(
                    protocol_number=protocol_number, aidoc_id=expected_aidoc_id, protocol_number_verified=protocol_number_verified)

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
            cleaned_inputs = utils.clean_inputs(protocol_number=args['protocolNumber'], version_number=args['versionNumber'],
                                                document_status=args['documentStatus'], qc_status=args['qcStatus'])
            protocol_number = cleaned_inputs.get('protocol_number', '')
            version_number = cleaned_inputs.get('version_number', '')
            document_status = cleaned_inputs.get('document_status', '')
            qc_status = cleaned_inputs.get('qc_status', '')

            if not protocol_number:
                logger.error(f"Invalid protocol_number received: {args}")
                return abort(404, INVALID_USER_INPUT.format(args))

            resources = get_latest_protocol(protocol_number=protocol_number, version_number=version_number, document_status=document_status,
                                            qc_status=qc_status, is_top_1_only=False)
            aligned_resources = utils.post_process_resource(
                resources, multiple_records=True)

            if aligned_resources:
                if isinstance(aligned_resources, list):
                    for resource in aligned_resources:
                        resource.documentStatus = resource.documentStatus.capitalize()
                if isinstance(aligned_resources, dict):
                    aligned_resources['documentStatus'] = aligned_resources.get(
                        'documentStatus', '').capitalize()
                    for ver in aligned_resources.get('allVersions', []):
                        ver['documentStatus'] = ver.get(
                            'documentStatus', '').capitalize()

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
            cleaned_inputs = utils.clean_inputs(
                protocol_number=args['protocolNumber'], aidoc_id=args['id'])
            protocol_number = cleaned_inputs.get('protocol_number', '')
            aidoc_id = cleaned_inputs.get('aidoc_id', '')

            if not protocol_number or not aidoc_id:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))

            resource = get_attr_soa_details(
                protocol_number=protocol_number, aidoc_id=aidoc_id)

            if len(resource) == 0:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/norm_soa_compare')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(norm_soa_compare_input)
    @ns.marshal_with(norm_soa_compare_get)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get Normalized SOA difference"""
        args = norm_soa_compare_input.parse_args()
        try:
            cleaned_inputs = utils.clean_inputs(
                protocol_number=args['protocolNumber'], aidoc_id=args['baseDocId'], compare_doc_id=args['compareDocId'])
            protocol_number = cleaned_inputs.get('protocol_number', '')
            aidoc_id = cleaned_inputs.get('aidoc_id', '')
            compare_doc_id = cleaned_inputs.get('compare_doc_id', '')

            if not protocol_number or not aidoc_id or not compare_doc_id:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))

            resource = get_attr_soa_compare(
                protocol_number=protocol_number, aidoc_id=aidoc_id, compare_doc_id=compare_doc_id)

            if len(resource) == 0:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/protocol_normalized_soa')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(protocol_soa_input)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get Protocol Normalized SOA"""
        args = protocol_soa_input.parse_args()
        try:
            cleaned_inputs = utils.clean_inputs(aidoc_id=args['id'])
            aidoc_id = cleaned_inputs.get('aidoc_id', '')

            if not aidoc_id:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))
            if args['operationValue'] == 'normalizedSOA':
                resource = get_normalized_soa_details(aidoc_id=aidoc_id)
            elif args['operationValue'] == 'SOATable':
                resource = get_normalized_soa_table(aidoc_id=aidoc_id)
            else:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            if len(resource) == 0:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))
    

@ns.route('/meta_data_summary')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(metadata_summary_input)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get metadata attributes"""
        args = metadata_summary_input.parse_args()
        try:
            op = args.get('op', '').strip()
            aidoc_id = args.get('aidocId', '').strip()
            field_name = args.get('fieldName', None)
            if isinstance(field_name, str):
                field_name = field_name.strip()

            if op == 'metadata' or op == 'metaparam':
                if aidoc_id:
                    resource = get_metadata_summary(op, aidoc_id, field_name)
                    if len(resource) == 0:
                        return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
                    else:
                        return resource
                else:
                    logger.error(f"Invalid aidocId received: {args}")
                    return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))
            else:
                logger.error(f"Invalid operation inputs received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))

        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/add_meta_data')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(metadata_summary_create)
    @ns.marshal_with(metadata_summary_add)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def put(self):
        """Add metadata attributes"""
        args = metadata_summary_create.parse_args()
        try:
            op = args.get('op', '').strip()
            aidoc_id = args.get('aidocId', '').strip()
            field_name = args.get('fieldName', '').strip()
            attributes = args['attributes']
            data = {}
            attr_list = []

            if op and aidoc_id:
                data['id'] = aidoc_id
                data['fieldName'] = field_name
                if attributes is not None:
                    for attrs in attributes:
                        attribute_name = attrs.get('attr_name', '').strip()
                        attribute_type = attrs.get('attr_type', '').strip()
                        attribute_value = attrs.get('attr_value', None)
                        if isinstance(attribute_value, str):
                            attribute_value = attribute_value.strip()
                        note_value = attrs.get('note', None)
                        if isinstance(note_value, str):
                            note_value = note_value.strip()
                        confidence_value = attrs.get('confidence', None)
                        if isinstance(confidence_value, str):
                            confidence_value = confidence_value.strip()
                        attr_list.append({"attributeName": attribute_name,
                                          "attributeType": attribute_type,
                                          "attributeValue": attribute_value,
                                          "note": note_value,
                                          "confidence": confidence_value})
                data['attributes'] = attr_list
                resource = add_metadata_summary(op, **data)

                if len(resource) == 0:
                    return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
                else:
                    return resource
            else:
                logger.error(f"Invalid op or aidocId received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))

        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/add_update_meta_data')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(metadata_summary)
    @ns.marshal_with(metadata_summary_update)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def post(self):
        """Update metadata attributes"""
        args = metadata_summary.parse_args()
        try:
            aidoc_id = args.get('aidocId', '').strip()
            field_name = args.get('fieldName', '').strip()
            attributes = args['attributes']
            data = {}
            attr_list = []
            if aidoc_id:
                data['id'] = aidoc_id
                data['fieldName'] = field_name
                if attributes is not None:
                    for attrs in attributes:
                        attribute_name = attrs.get('attr_name', '').strip()
                        attribute_type = attrs.get('attr_type', '').strip()
                        attribute_value = attrs.get('attr_value', None)
                        if isinstance(attribute_value, str):
                            attribute_value = attribute_value.strip()
                        note_value = attrs.get('note', None)
                        if isinstance(note_value, str):
                            note_value = note_value.strip()
                        confidence_value = attrs.get('confidence', None)
                        if isinstance(confidence_value, str):
                            confidence_value = confidence_value.strip()
                        attr_list.append({"attributeName": attribute_name,
                                          "attributeType": attribute_type,
                                          "attributeValue": attribute_value,
                                          "note": note_value,
                                          "confidence": confidence_value})
                data['attributes'] = attr_list
                resource = update_metadata_summary(field_name, **data)

                if len(resource) == 0:
                    return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
                else:
                    return resource
            else:
                logger.error(f"Invalid aidocId received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/delete_meta_data')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(metadata_detele_summary)
    @ns.marshal_with(metadata_summary_delete)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def delete(self):
        """Delete metadata attributes"""
        args = metadata_detele_summary.parse_args()
        try:
            op = args.get('op', '').strip()
            aidoc_id = args.get('aidocId', '').strip()
            field_name = args.get('fieldName', '').strip()
            attributes = args.get('attributeNames')
            data = {}
            attr_list = []
            if op and aidoc_id and field_name:
                data['id'] = aidoc_id
                data['fieldName'] = field_name
                if attributes is not None:
                    for attrs in attributes:
                        attr_list.append({'attributeName': attrs})
                data['attributes'] = attr_list
                resource = delete_metadata_summary(op, **data)
                if len(resource) == 0:
                    return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
                else:
                    return resource
            else:
                logger.error(
                    f"Invalid operation or aidocId or fieldName received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))

        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/get_protocols')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(latest_protocol_input_by_date_range)
    @ns.marshal_with(latest_protocol_get_by_date_range)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get all the protocols processed in PD based on input parameters"""
        args = latest_protocol_input_by_date_range.parse_args()
        try:
            cleaned_inputs = utils.clean_inputs(document_status=args['documentStatus'], qc_status=args['qcStatus'],
                                                version_date=args['versionDate'], end_date=args['endDate'],
                                                start_date=args['startDate'], approval_date=args['approvalDate'],
                                                upload_date=args['uploadDate']
                                                )
            version_date = cleaned_inputs.get('version_date', '')
            document_status = cleaned_inputs.get('document_status', '')
            start_date = cleaned_inputs.get('start_date', '')
            end_date = cleaned_inputs.get('end_date', '')
            upload_date = cleaned_inputs.get('upload_date', '')
            approval_date = cleaned_inputs.get('approval_date', '')
            qc_status = cleaned_inputs.get('qc_status', '')

            resources = get_protocols_by_date_time_range(approval_date=approval_date, qc_status=qc_status,
                                                         upload_date=upload_date,
                                                         start_date=start_date, end_date=end_date,
                                                         version_date=version_date,
                                                         document_status=document_status)

            if resources is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resources
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))
