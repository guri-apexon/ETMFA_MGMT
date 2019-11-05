import os, uuid, logging, requests, json

from flask_restplus import Namespace, Resource, fields, reqparse, abort
from flask import current_app, send_from_directory, request, make_response, Flask, abort, g
from functools import wraps
import werkzeug
import datetime
import os.path


from ..api import api

from ...db import (
    create_processing_config,
    get_processing_config,
    get_root_dir,
    save_doc_processing,
    save_doc_processing_duplicate,
    save_doc_feedback,
    get_doc_resource_by_id,
    get_doc_processing_by_id,
    get_doc_processed_by_id,
    get_doc_proc_metrics_by_id,
    get_doc_status_processing_by_id,
    upsert_attributevalue,
    get_attribute_dict
    )

from ...consts import Consts as consts
#from ...db import db_context
logger = logging.getLogger(consts.LOGGING_NAME)

from ...messaging.messagepublisher import MessagePublisher
from ...messaging.models.Triage_Request import TriageRequest
from ...messaging.models.feedback_request import feedbackrequest


from .serializers import *

ns = api.namespace('eTMFA', path='/v1/documents', description='REST endpoints for eTMFA workflows.')


@ns.route('/')
@ns.response(500, 'Server error.')
class DocumentprocessingAPI(Resource):
    @ns.expect(eTMFA_object_post)
    @ns.marshal_with(eTMFA_object_get)
    @ns.response(400, 'Invalid Request.')
    @ns.response(200, 'Success')
    def post(self):
        """Create document Processing REST object and returns document Processing API object """

        args = eTMFA_object_post.parse_args()

        if (args['customer'] is None) or (args['protocol'] is None) or (args['documentClass'] is None) or (args['file'] is None):
           return abort(400, 'Invalid Request.')
        else:
            # Generate ID
            _id = uuid.uuid4()
            _id = str(_id)
            path = build_processing_dir(_id)

            # get save path and output path
            processing_dir = build_processing_dir(_id)
            file = args['file']
            filename_main = file.filename

            # Convert file names to shorter length by replacing original filename with timestamp

            ts = datetime.datetime.now().timestamp()
            fileprefix = str(int(ts * 1000000))
            filesufix = os.path.splitext(filename_main)[1]
            filename = fileprefix + filesufix

            # build file path in the processing directory
            file_path = os.path.join(processing_dir, filename)

            # Save document in the processing directory
            file.save(file_path)
            g.aidocid = _id

            customer            = args['customer'] if args['customer'] is not None else ' '              #customer check
            protocol            = args['protocol'] if args['protocol'] is not None else ' '              #protocol check
            country             = args['country'] if args['country'] is not None else ' '                #country check
            site                = args['site'] if args['site'] is not None else ' '                      #site check
            document_class      = args['documentClass'] if args['documentClass'] is not None else ' '  #document class check
            tmf_ibr             = args['tmfIbr'] if args['tmfIbr'] is not None else ' '                #environment check
            blinded             = args['unblinded'] if args['unblinded'] is not None else True           #document blinded/unblinded
            tmf_environment     = args['tmfEnvironment'] if args['tmfEnvironment'] is not None else ' '
            received_date       = args['receivedDate'] if args['receivedDate'] is not None else ' '     #received date check
            site_personnel_list = args['sitePersonnelList'] if args['sitePersonnelList'] is not None else ' '
            priority            = args['priority'] if args['priority'] is not None else ' '               #priority check

            #saved_resource = save_doc_processing(args, _id, file_path)
            save_doc_processing(args, _id, file_path)
            duplicatecheck = save_doc_processing_duplicate(args, _id, filename_main, file_path)

            BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
            EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']

            msg_f = TriageRequest(_id, filename_main, file_path, customer, protocol, country, site, document_class,
                            tmf_ibr, blinded, tmf_environment, received_date, site_personnel_list, priority, duplicatecheck)

            MessagePublisher(BROKER_ADDR, EXCHANGE, logging.getLogger(consts.LOGGING_NAME)).send_obj(msg_f)
            #print("Message for initial puh: ", TriageRequest.QUEUE_NAME)
            #logger.info("Sent message on queue: {}, {}".format(TriageRequest.QUEUE_NAME, _id))

            # Return response object
            return get_doc_processing_by_id(_id, full_mapping=True)


#
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

        g.aidocid                     = id
        feedbackdata                  = request.json
        id_fb                         = feedbackdata['id']
        feedback_source               = feedbackdata['feedbackSource']
        customer                      = feedbackdata['customer']
        protocol                      = feedbackdata['protocol']
        country                       = feedbackdata['country']
        site                          = feedbackdata['site']
        document_class                = feedbackdata['documentClass']
        document_date                 = feedbackdata['documentDate']
        document_classification       = feedbackdata['documentClassification']
        name                          = feedbackdata['name']
        language                      = feedbackdata['language']
        document_rejected             = feedbackdata['documentRejected']
        attribute_auxillary_list      = feedbackdata['attributeAuxillaryList']

        resourcefound = get_doc_resource_by_id(id)
        if resourcefound == None:
            return abort(404, 'Document Processing resource not found for id: {}'.format(id))

        saved_resource = save_doc_feedback(id, feedbackdata)


        # Send async FormattingDeconstructionRequest
        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']

        message_publisher = MessagePublisher(BROKER_ADDR, EXCHANGE, logging.getLogger(consts.LOGGING_NAME))

        # Send FeedbackRequest
        feedback_req_msg = feedbackrequest(
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
            attribute_auxillary_list
        )
        message_publisher.send_obj(feedback_req_msg)


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
        if resource == None:
            return abort(404, 'Document Processing resource not found for id: {}'.format(id))
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
            if resource == None:
                return abort(404, 'Document Processing resource not found for id: {}'.format(id))
            else:
                return resource
        except ValueError as e:
            return abort(500, 'Server error.')


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
            if resource == None:
                return abort(404, 'Document Processing resource not found id: {}'.format(id))
            else:
                return resource
        except ValueError as e:
            return abort(500, 'Server error.')


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
            if resource == None:
                return abort(404, 'Document Processing resource not found for id: {}'.format(id))
            else:
                return resource
        except ValueError as e:
            return abort(500, 'Server error.')


# Utility Functions

def build_processing_dir(ID):
    PROCESSING_DIR = get_root_dir()

    path = os.path.join(PROCESSING_DIR, str(ID) + "/")
    if not os.path.isdir(path):
        os.makedirs(path)

    return path