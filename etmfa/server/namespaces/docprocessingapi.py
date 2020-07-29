import logging
import uuid
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
    get_doc_proc_metrics_by_id,
    get_doc_status_processing_by_id,
    upsert_attributevalue
)
from etmfa.messaging.messagepublisher import MessagePublisher
from etmfa.messaging.models.triage_request import TriageRequest
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
    document_processing_object_put_get
)
from flask import current_app, request, abort, g
from flask_restplus import Resource, abort

logger = logging.getLogger(consts.LOGGING_NAME)
DOCUMENT_NOT_FOUND = 'Document Processing resource not found for id: {}'
SERVER_ERROR = 'Server error: {}'

ns = api.namespace('eTMFA', path='/v1/documents', description='REST endpoints for eTMFA workflows.')


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

        customer = args['customer'] if args['customer'] is not None else ' '  # customer check
        protocol = args['protocol'] if args['protocol'] is not None else ' '  # protocol check
        country = args['country'] if args['country'] is not None else ' '  # country check
        site = args['site'] if args['site'] is not None else ' '  # site check
        document_class = args['documentClass'] if args['documentClass'] is not None else ' '  # document class check
        document_class = document_class.lower()
        if document_class == DocumentClass.STUDY.value:
            document_class = DocumentClass.CORE.value
        tmf_ibr = args['tmfIbr'] if args['tmfIbr'] is not None else ' '  # environment check
        blinded = args['unblinded'] if args['unblinded'] is not None else True  # document blinded/unblinded
        tmf_environment = args['tmfEnvironment'] if args['tmfEnvironment'] is not None else ' '
        received_date = args['receivedDate'] if args['receivedDate'] is not None else ' '  # received date check
        site_personnel_list = args['sitePersonnelList'] if args['sitePersonnelList'] is not None else ' '
        priority = args['priority'] if args['priority'] is not None else ' '  # priority check
        user_id = args['userId'] if args['userId'] is not None else ' '

        save_doc_processing(args, _id, str(file_path))
        duplicatecheck = save_doc_processing_duplicate(args, _id, filename_main, str(file_path))

        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']
        print("reached triage request sent")
        post_req_msg = TriageRequest(_id, filename_main, str(file_path), customer, protocol, country, site,
                                     document_class,
                                     tmf_ibr, blinded, tmf_environment, received_date, site_personnel_list, priority, user_id,
                                     duplicatecheck)

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


@ns.route('/<string:id>/attributes')
@ns.response(200, 'Success.')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.marshal_with(eTMFA_attributes_get)
    def get(self, id):
        """Get the document processing object attributes"""
        try:
            g.aidocid = id
            resource = get_doc_processed_by_id(id, full_mapping=True)
            if resource is None:
                return abort(404, DOCUMENT_NOT_FOUND.format(id))
            else:
                return resource
        except ValueError as e:
            logger.error(SERVER_ERROR.format(e))
            return abort(500, SERVER_ERROR.format(e))
