import logging
import uuid
import hashlib
from dataclasses import asdict
from etmfa.server.config import Config
from flask import send_from_directory, make_response
from http import HTTPStatus
from pathlib import Path
import json

from flask import request, g
from flask_restplus import Resource, abort, reqparse
from etmfa.auth import authenticate
from etmfa.consts import Consts as consts
from etmfa.db import feedback_utils as fb_utlis, check_work_flow_name
from etmfa.db.models import pd_dipa_view_data
from etmfa.db.db import db_context
from .confidence_metric import fetch_records_from_db
from etmfa.db.soa_operations import (
    add_study_procedure,
    add_normalized_data_for_study_procedure,
    add_study_visit,
    add_normalized_data_for_study_visit,
    update_normalized_soa_cell_value,
    delete_normalized_soa_cell_value_by_column,
    delete_normalized_soa_cell_value_by_row,
    create_message,
    create_message_add_operation,
)
from etmfa.db import (
    get_work_flow_status_by_id,
    get_details_by_elm,
    check_if_document_processed,
    create_doc_processing_status,
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
    delete_metadata_summary,
    get_dipaview_details_by_id,
    get_dipa_data_by_category
)
from etmfa.db import utils
from etmfa.consts import ACCORDIAN_DOC_ID
from etmfa.workflow.messaging import MsqType
from etmfa.workflow.messaging.models.triage_request import TriageRequest
from etmfa.server.api import api
from etmfa.workflow.db.db_utils import get_all_workflows_from_db, get_wf_by_doc_id
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
    protocol_soa_post,
    metadata_summary_input,
    metadata_summary_create,
    metadata_summary_update,
    metadata_summary_add,
    metadata_summary,
    metadata_detele_summary,
    dipadata_details_get,
    dipadata_details_input,
    metadata_summary_delete,
    dipa_view_data,
    fetch_workflows_by_doc_id,
    fetch_confidence_score
)
from etmfa.workflow.default_workflows import DWorkFLows, DEFAULT_WORKFLOWS
from etmfa.workflow import WorkFlowClient
from etmfa.workflow.messaging.models.generic_request import DocumentRequest, CompareRequest
from etmfa.db.models.work_flow_status import WorkFlowStatus
from .cdc_util import CdcThread
from flask import jsonify
from etmfa.workflow.wf_manager import WorkFlowManager
from ...consts.constants import DEFAULT_WORKFLOW_NAME
from etmfa.workflow import WorkFlowParamMissing
logger = logging.getLogger(consts.LOGGING_NAME)

INVALID_USER_INPUT = 'Invalid user input(s) received: {}'
DOCUMENT_NOT_FOUND = 'Document resource is not found for the requested input(s): {}'
DUPLICATE_DOCUMENT_REQUEST = 'Duplicate document request '
DOCUMENT_MISSING_FROM_METADATA_TABLE = 'Document missing from protocol metadata table'
SERVER_ERROR = 'Server error: {}'
DOCUMENT_COMPARISON_ALREADY_PRESENT = 'Comparison already present for given protocols'
MISSING_INPUT = 'Mandatory parameter {} not provided'
INVALID_OPERATION = 'invalid operation'
ns = api.namespace('PD', path='/v1/documents',
                   description='REST endpoints for PD workflows.')

def get_params(args):
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

    return source_filename, version_number, protocol, document_status, environment,\
        source_system, sponsor, study_status, amendment_number, project_id, indication,\
        molecule_device, user_id, workflow_name, duplicate_check


def generate_doc_meta_hash(file_path):
    """meta hash"""
    with open(file_path, 'rb') as fp:
        data = fp.read()
        result = hashlib.sha256(data)
        return result.hexdigest()


def register_custom_flows(work_flow_list, work_flow_name, _id, doc_id):
    message, response_status = None, None
    if work_flow_list and Config.WORK_FLOW_RUNNER:
        wf_client = WorkFlowClient()
        if work_flow_name:
            message, response_status = wf_client.send_msg(work_flow_name, _id, "",
                                                          {"work_flow_list": work_flow_list,
                                                           "doc_id": doc_id},
                                                          MsqType.ADD_CUSTOM_WORKFLOW.value)
        else:
            work_flow_name = check_work_flow_name(work_flow_name, work_flow_list)
            message, response_status = wf_client.send_msg(work_flow_name, _id, "",
                                                          {"work_flow_list": work_flow_list,
                                                           "doc_id": doc_id},
                                                          MsqType.RUN_DEFAULT_WORKFLOW.value)
    return message, response_status

@ns.route('/run_work_flow')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
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
        doc_id = args['docId']
        work_flow_name = args['workFlowName']
        work_flow_list = args['workFlowList']
        try:
            fields = get_details_by_elm(
                WorkFlowStatus, WorkFlowStatus.work_flow_id, doc_id)
            doc_file_path = fields['documentFilePath']
            protocol = fields['protocol_name']

        except Exception as e:
            logger.error(
                'requested document is not in workflow status table' + str(doc_id) + str(e))
            abort(404, DOCUMENT_MISSING_FROM_METADATA_TABLE)

        doc_uid = None
        _id = str(uuid.uuid4())
        message, response_status = register_custom_flows(work_flow_list,work_flow_name,_id,doc_id)
        if not response_status and work_flow_list and Config.WORK_FLOW_RUNNER:
            return abort(400, message)

        if not work_flow_list:
            work_flow_graph = DEFAULT_WORKFLOWS.get(work_flow_name, None)
            if not work_flow_graph or len(work_flow_graph) < 1:
                abort(404, DOCUMENT_MISSING_FROM_METADATA_TABLE)

            start_service_name = work_flow_graph[0].get('service_name', None)
            if not start_service_name:
                abort(404, str(WorkFlowParamMissing(work_flow_name)))

        work_flow_name = check_work_flow_name(work_flow_name, work_flow_list)

        create_doc_processing_status(
            _id, doc_id, doc_uid, work_flow_name, doc_file_path, protocol)
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
        _file = args['file']
        filename_main = _file.filename

        # build file path in the processing directory
        filepath = processing_dir.joinpath(filename_main)
        # Save document in the processing directory
        _file.save(str(filepath))
        logger.info("Document saved at location: {}".format(filepath))

        source_filename, version_number, protocol, document_status, environment,\
            source_system, sponsor, study_status, amendment_number, project_id, indication,\
            molecule_device, user_id, workflow_name, duplicate_check = get_params(
                args)

        feedback_run_id = 0

        filepath = str(filepath)
        if duplicate_check:
            doc_uid = generate_doc_meta_hash(filepath)
            is_processed, duplicate_docs = check_if_document_processed(doc_uid)
            if is_processed:
                return abort(409, json.dumps({'duplicate_docs': duplicate_docs}, default=str))
        else:
            doc_uid = _id

        create_doc_processing_status(
            _id, _id, doc_uid, workflow_name, filepath, protocol)
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

    def get_params(self, args):
        """All Param"""
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

        return source_filename, version_number, protocol, document_status, environment,\
            source_system, sponsor, study_status, amendment_number, project_id, indication,\
            molecule_device, user_id, workflow_name, duplicate_check


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
                return abort(404, DOCUMENT_NOT_FOUND.format(id))
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

            resources = get_latest_protocol(protocol_number=protocol_number, aidoc_id=aidoc_id,
                                            version_number=version_number,
                                            approval_date=approval_date, document_status=document_status,
                                            is_top_1_only=True)
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
        expected_aidoc_id = ''
        args = latest_protocol_contents_input.parse_args()

        try:
            protocol_number = args['protocolNumber'] if args['protocolNumber'] is not None else ' '
            aidoc_id = args['id'] if args['id'] is not None else ''
            approval_date = args['approvalDate'] if args['approvalDate'] is not None else ''
            version_number = args['versionNumber'] if args['versionNumber'] is not None else ''
            document_status = args['documentStatus'] if args['documentStatus'] is not None else ''

            if not aidoc_id:
                resources = get_latest_protocol(protocol_number=protocol_number, aidoc_id=aidoc_id,
                                                version_number=version_number,
                                                approval_date=approval_date, document_status=document_status,
                                                is_top_1_only=True)
                aligned_resources = utils.post_process_resource(
                    resources, multiple_records=False)
                expected_aidoc_id = '' if aligned_resources is None else aligned_resources['id']
            else:
                expected_aidoc_id = aidoc_id

            if expected_aidoc_id:
                resource = get_file_contents_by_id(
                    protocol_number=protocol_number, aidoc_id=expected_aidoc_id)

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
            cleaned_inputs = utils.clean_inputs(protocol_number=args['protocolNumber'],
                                                version_number=args['versionNumber'],
                                                document_status=args['documentStatus'], qc_status=args['qcStatus'])
            protocol_number = cleaned_inputs.get('protocol_number', '')
            version_number = cleaned_inputs.get('version_number', '')
            document_status = cleaned_inputs.get('document_status', '')
            qc_status = cleaned_inputs.get('qc_status', '')

            if not protocol_number:
                logger.error(f"Invalid protocol_number received: {args}")
                return abort(404, INVALID_USER_INPUT.format(args))

            resources = get_latest_protocol(protocol_number=protocol_number, version_number=version_number,
                                            document_status=document_status,
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
            footnote = args.get('footnotes', False)
            if not aidoc_id:
                logger.error(f"Invalid user inputs received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))
            operation_value = args['operationValue'] if args.get(
                'operationValue', None) else 'normalizedSOA'
            if operation_value == 'normalizedSOA':
                resource = get_normalized_soa_details(aidoc_id=aidoc_id)
            elif operation_value == 'SOATable':
                resource = get_normalized_soa_table(
                    aidoc_id=aidoc_id, footnote=footnote)
            else:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            if len(resource) == 0:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))

    @ns.expect(protocol_soa_post)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def post(self):
        """
        Create, Update and delete operations
        """
        args = protocol_soa_post.parse_args()
        message = ""
        try:
            session = db_context.session()
            operation = args.get('operation').strip()
            sub_type = args.get('sub_type').strip()
            table_props = args.get('table_props')

            # For row addition
            if operation == 'add' and sub_type == 'add_row':
                study_procedure = add_study_procedure(session, table_props)
                normalized_data = add_normalized_data_for_study_procedure(
                    session, table_props)
                session.commit()
                message = create_message_add_operation(study_procedure, normalized_data, sub_type)

            # For column addition
            elif operation == 'add' and sub_type == 'add_column':
                study_visit = add_study_visit(session, table_props)
                normalized_data = add_normalized_data_for_study_visit(
                    session, table_props)
                session.commit()
                message = create_message_add_operation(study_visit, normalized_data, sub_type)

            # For cell value updation
            elif operation == 'update':
                update_cell = update_normalized_soa_cell_value(
                    session, table_props, sub_type)
                session.commit()
                message = create_message(update_cell, operation, sub_type)

            # For column deletion
            elif operation == 'delete' and sub_type == 'delete_column':
                delete_column = delete_normalized_soa_cell_value_by_column(
                    session, table_props)
                session.commit()
                message = create_message(delete_column, operation, sub_type)

            # For row deletion
            elif operation == 'delete' and sub_type == 'delete_row':
                delete_row = delete_normalized_soa_cell_value_by_row(
                    session, table_props)
                session.commit()
                message = create_message(delete_row, operation, sub_type)
            else:
                abort(INVALID_USER_INPUT, INVALID_USER_INPUT.format(args))
            if message == "":
                return {"status": 404, "response": "Error in processing your request."}
            else:
                return {"status": 200, "response": message}
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
            aidoc_id = args.get('aidocId').strip() if isinstance(args.get('aidocId'), str) else ''
            field_name = args.get('fieldName').strip() if isinstance(args.get('fieldName'), str) else ''
            if not aidoc_id:
                aidoc_id = ACCORDIAN_DOC_ID

            if aidoc_id:
                resource = get_metadata_summary(op, aidoc_id, field_name)
                if len(resource) == 0:
                    return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
                else:
                    return resource

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
            data, attr_list = {}, []
            op = args.get('op', '').strip()
            aidoc_id = args.get('aidocId', '').strip()
            field_name = args.get('fieldName', '').strip()
            if not aidoc_id:
                aidoc_id = ACCORDIAN_DOC_ID
            if not field_name and aidoc_id != ACCORDIAN_DOC_ID:
                field_name = "summary_extended"
            attributes = args['attributes']

            if attributes:
                for attrs in attributes:
                    attribute_name = attrs.get('attr_name').strip() if isinstance(attrs.get('attr_name'), str) else ''
                    attribute_type = attrs.get('attr_type').strip() if isinstance(attrs.get('attr_type'), str) else ''
                    attribute_value = attrs.get('attr_value', None)
                    note_value = attrs.get('note').strip() if isinstance(attrs.get('note'), str) else ''
                    confidence_value = attrs.get('confidence').strip() if isinstance(attrs.get('confidence'), str) else ''
                    user_id = attrs.get('user_id').strip() if isinstance(attrs.get('user_id'), str) else ''
                    display_name = attrs.get('display_name').strip() if isinstance(attrs.get('display_name'), str) else ''

                    attr_list.append({"attribute_name": attribute_name,
                                        "attribute_type": attribute_type,
                                        "attribute_value": attribute_value,
                                        "note": note_value,
                                        "confidence": confidence_value,
                                        "display_name": display_name,
                                        "user_id": user_id})

            data = {'id': aidoc_id, 'fieldName': field_name,
                    'attributes': attr_list}
            resource = add_metadata_summary(op, **data)

            if len(resource) == 0:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource

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
            if not aidoc_id:
                aidoc_id = ACCORDIAN_DOC_ID
            field_name = args.get('fieldName', '').strip()
            if not field_name and aidoc_id != ACCORDIAN_DOC_ID:
                field_name = "summary_extended"
            attributes = args['attributes']
            data, attr_list = {}, []
            if attributes:
                for attrs in attributes:
                    attribute_id = attrs.get('attr_id').strip() if isinstance(attrs.get('attr_id'), str) else ''
                    attribute_name = attrs.get('attr_name').strip() if isinstance(attrs.get('attr_name'), str) else ''
                    attribute_type = attrs.get('attr_type').strip() if isinstance(attrs.get('attr_type'), str) else ''
                    attribute_value = attrs.get('attr_value', None)
                    note_value = attrs.get('note').strip() if isinstance(attrs.get('note'), str) else ''
                    confidence_value = attrs.get('confidence').strip() if isinstance(attrs.get('confidence'), str) else ''
                    user_id = attrs.get('user_id').strip() if isinstance(attrs.get('user_id'), str) else ''
                    display_name = attrs.get('display_name').strip() if isinstance(attrs.get('display_name'), str) else ''

                    attr_list.append({"attribute_name": attribute_name,
                                        "attribute_type": attribute_type,
                                        "attribute_value": attribute_value,
                                        "attr_id": attribute_id,
                                        "note": note_value,
                                        "confidence": confidence_value,
                                        "display_name": display_name,
                                        "user_id": user_id})

            data = {'id': aidoc_id, 'fieldName': field_name,
                    'attributes': attr_list}
            resource = update_metadata_summary(field_name, **data)

            if len(resource) == 0:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource

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
            soft_delete = args.get('softDelete')
            aidoc_id = args.get('aidocId').strip() if isinstance(args.get('aidocId'), str) else ''
            if not aidoc_id:
                aidoc_id = ACCORDIAN_DOC_ID
            field_name = args.get('fieldName', '').strip() if isinstance(args.get('fieldName'), str) else ''
            attributes = args.get('attributeNames')
            attribute_ids= args.get('attributeIds')
            attribute_ids=[] if not attribute_ids else attribute_ids
            data, attr_list = {}, []
            attr_id_len = len(attribute_ids)

            if attributes:
                for attr_idx,attrs in enumerate(attributes):
                    attr_id = None if (not attr_id_len or attr_idx > attr_id_len) else attribute_ids[attr_idx]
                    attr_list.append({'attribute_name': attrs,'attr_id':attr_id})

            data = {'id': aidoc_id, 'fieldName': field_name,
                    'attributes': attr_list, 'softDelete': soft_delete}

            resource = delete_metadata_summary(op, **data)
            if len(resource) == 0:
                return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
            else:
                return resource

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


# DIPA view
@ns.route('/get_dipadata_by_doc_id')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(dipadata_details_get)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get dipadata attributes"""
        args = dipadata_details_get.parse_args()
        try:
            aidoc_id = args['doc_id']

            if aidoc_id:
                resource = get_dipaview_details_by_id(aidoc_id)

                if len(resource) == 0:
                    return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
                else:
                    return jsonify({"dipa_resource": resource})
            else:
                logger.error(f"Invalid aidocId received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))

        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/get_dipadata_by_category')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(dipadata_details_input)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get dipadata JSON for given doc_id and Category"""
        args = dipadata_details_input.parse_args()
        try:
            _id = args['id']
            aidoc_id = args['doc_id']
            category = args['category'] if args['category'] is not None else ' '

            if aidoc_id:
                resource = get_dipa_data_by_category(_id, aidoc_id, category)

                if len(resource) == 0:
                    return abort(HTTPStatus.NOT_FOUND, DOCUMENT_NOT_FOUND.format(args))
                else:
                    return jsonify({"dipa_resource": resource})
            else:
                logger.error(f"Invalid aidocId received: {args}")
                return abort(HTTPStatus.NOT_FOUND, INVALID_USER_INPUT.format(args))

        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))

@ns.route('/update_dipa_data')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(dipa_view_data)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    @ns.response(400, 'Bad Request')
    @api.doc(security='apikey')
    @authenticate
    def put(self):
        """Update/Add/Delete dipa view data"""
        args = dipa_view_data.parse_args()
        _id = args['id']
        doc_id = args.get('doc_id')
        link_id_1 = args.get('link_id_1')
        link_id_2 = args.get('link_id_2')
        link_id_3 = args.get('link_id_3')
        link_id_4 = args.get('link_id_4')
        link_id_5 = args.get('link_id_5')
        link_id_6 = args.get('link_id_6')
        user_id = args.get('userId')
        user_name = args.get('userName')
        try:
            data_dict = {"doc_id": doc_id, "editorUserId": user_id, "link_id_1": link_id_1, "link_id_2": link_id_2,
                         "link_id_3": link_id_3, "link_id_4": link_id_4, "link_id_5": link_id_5, "link_id_6": link_id_6,
                         "user_name": user_name, "dipa_data": args['dipa_data']}
            result = pd_dipa_view_data.DipaViewHelper.upsert(_id, data_dict)
            if result is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(args))
            else:
                return {"status": 200, "response": "Successfully Inserted Data in DB"}
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))

@ns.route('/get_all_workflows')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document Processing resource not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        try:
            default_workflows, custom_workflows = get_all_workflows_from_db()
            return {"Status": 200, "default_workflows": default_workflows,
                    "custom_workflows": custom_workflows}
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/cdc')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class CdcAPI(Resource):
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'CDC enabling not found.')
    @api.doc(security='apikey')
    @authenticate
    def post(self):
        try:
            operation = request.args.get('op')
            if operation == 'enable_cdc':

                try:
                    session = db_context.session()
                    latest_work = session.query(WorkFlowStatus).filter_by(protocol_name='running_cdc',
                                                                          work_flow_name='CDC',
                                                                          status='RUNNING').first()
                    if latest_work:
                        return {'id': latest_work.work_flow_id, 'status': latest_work.status}
                    else:
                        new_work = WorkFlowStatus(work_flow_id=str(uuid.uuid4()), protocol_name='running_cdc',
                                                  work_flow_name='CDC', status='RUNNING')
                        session.add(new_work)
                        session.commit()
                        CdcThread(new_work.work_flow_id).start()
                        return {'id': new_work.work_flow_id, 'status': new_work.status}
                except ValueError as e:
                    logger.error(SERVER_ERROR.format(e))
                    return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))
            else:
                return abort(HTTPStatus.BAD_REQUEST, INVALID_OPERATION)

        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/cdc_status/<string:id>/')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class CdcAPI(Resource):
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'CDC enabling not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self, id):
        try:
            try:
                session = db_context.session()
                latest_work = session.query(
                    WorkFlowStatus).filter_by(work_flow_id=id).first()
                if latest_work:
                    return {'id': latest_work.work_flow_id, 'status': latest_work.status,
                            'operation': latest_work.protocol_name}
                else:
                    logger.info("Status id not found")
                    return abort(HTTPStatus.NOT_FOUND, "Not found")
            except ValueError as e:
                return abort(HTTPStatus.BAD_REQUEST, INVALID_OPERATION)
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))


@ns.route('/get_workflows_by_doc_id')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Work Flows not Found')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        try:
            args = fetch_workflows_by_doc_id.parse_args()
            doc_id = args['doc_id']
            days = args['days']
            wf_num = args['wf_num']
            result = get_wf_by_doc_id(doc_id, days, wf_num)
            return {"Status": "200", "wfData": result}
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))


@ns.route('/get_confidence_matrix')
@ns.response(HTTPStatus.INTERNAL_SERVER_ERROR, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(fetch_confidence_score)
    @ns.response(HTTPStatus.OK, 'Success.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Confidence Matrix not Found')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        try:
            args = fetch_confidence_score.parse_args()
            sponsor_name = args['sponsorName']
            doc_id = args['doc_id']
            doc_status = args['docStatus']
            confidence_score = fetch_records_from_db(sponsor_name,
                                                     doc_status=doc_status, doc_id=doc_id)
            return confidence_score
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(HTTPStatus.INTERNAL_SERVER_ERROR, SERVER_ERROR.format(e))
