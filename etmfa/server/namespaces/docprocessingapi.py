import os, uuid, logging, requests, json

from flask_restplus import Namespace, Resource, fields, reqparse, abort
from flask import current_app, send_from_directory, request
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


from ...messaging.messagepublisher import MessagePublisher
from ...messaging.models.Triage_Request import TriageRequest
from ...messaging.models.feedback_request import feedbackrequest

from .serializers import *

ns = api.namespace('eTMFA', path='/v1/documents', description='REST endpoints for eTMFA workflows.')


@ns.route('/')
@ns.response(500, 'Server error')
class DocumentprocessingAPI(Resource):
    @ns.expect(eTMFA_object_post)
    @ns.marshal_with(eTMFA_object_get)
    @ns.response(201, 'Document processing resource created.')
    def post(self):
        """Create document Processing REST object and returns document Processing API object """

        # Generate processing dir
        args = eTMFA_object_post.parse_args()

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

        customer = args['Customer'] if args['Customer'] is not None else ' '                    #customer check
        protocol = args['Protocol'] if args['Protocol'] is not None else ' '                    #protocol check
        country  = args['Country'] if args['Country'] is not None else ' '                      #country check
        site = args['Site'] if args['Site'] is not None else ' '                                #site check
        document_class = args['Document_Class'] if args['Document_Class'] is not None else ' '  #document class check
        tmf_ibr = args['TMF_IBR'] if args['TMF_IBR'] is not None else ' '                       #environment check
        blinded = args['Blinded']                                                               #document blinded/unblinded
        tmf_environment = args['TMF_Environment'] if args['TMF_Environment'] is not None else ' '
        received_date = args['Received_Date'] if args['Received_Date'] is not None else ' '     #received date check
        site_personnel_list = args['site_personnel_list'] if args['site_personnel_list'] is not None else ' '
        priority = args['Priority'] if args['Priority'] is not None else ' '                    #priority check

        saved_resource = save_doc_processing(args, _id, file_path)
        duplicatecheck = save_doc_processing_duplicate(args, _id, file_path)

        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']

        msg_f = TriageRequest(_id, filename_main, file_path, customer, protocol, country, site, document_class,
                              tmf_ibr, blinded, tmf_environment, received_date, site_personnel_list, priority, duplicatecheck)

        MessagePublisher(BROKER_ADDR, EXCHANGE, logging.getLogger(consts.LOGGING_NAME)).send_obj(msg_f)

        # Return response object
        return get_doc_processing_by_id(_id, full_mapping=True)


@ns.route('/<string:id>/key/value')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error')
class DocumentprocessingAPI(Resource):
    @ns.expect(metadata_post)
    @ns.marshal_with(eTMFA_attributes_get)
    @ns.response(201, 'Document processing resource returned OK')
    def patch(self, id):
        """Update document attributes with key value """
        md = request.json
        for m in md['metadata']:
            upsert_attributevalue(id, m['name'], m['val'])
        return get_doc_processed_by_id(id)

#
# @ns.route('/<string:id>/get_attribute/key')
# @ns.response(404, 'Document processing resource not found.')
# @ns.response(500, 'Server error')
# class DocumentprocessingAPI(Resource):
#     @ns.expect(metadata_get)
#     @ns.marshal_with(metadata_post)
#     @ns.response(201, 'Document processing resource returned OK')
#     def get(self, id):
#         md = request.json
#         return get_attributevalue(id, md)
#

@ns.route('/<string:id>/status')
@ns.response(404, 'Document Processing resource not found.')
@ns.response(500, 'Server error')
class DocumentprocessingAPI(Resource):
    @ns.marshal_with(eTMFA_object_get_status)
    @ns.response(200, 'Document procesing resource returned OK')
    def get(self, id):
        """Get document processing object status. This includes any locations of processed documents"""
        try:
            return get_doc_status_processing_by_id(id, full_mapping=True)
        except ValueError as error:
            return abort(404, 'No document processing resource exists for this id.')

#
@ns.route('/<string:id>/feedback')
@ns.response(200, 'Document processing resource returned OK')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error')
class DocumentprocessingAPI(Resource):
    @ns.expect(document_processing_object_put)
    @ns.marshal_with(document_processing_object_put_get)
    def put(self, id):
        """Feedback attributes to document processed"""

        # format data for finalisation service to update IQVDocument
        feedbackdata                  = request.json
        id_fb                         = feedbackdata['id']
        feedback_source               = feedbackdata['feedback_source']
        customer                      = feedbackdata['customer']
        protocol                      = feedbackdata['protocol']
        country                       = feedbackdata['country']
        site                          = feedbackdata['site']
        document_class                = feedbackdata['document_class']
        document_date                 = feedbackdata['document_date']
        document_classification       = feedbackdata['document_classification']
        name                          = feedbackdata['name']
        language                      = feedbackdata['language']
        document_rejected             = feedbackdata['document_rejected']
        attribute_auxillary_list      = feedbackdata['attribute_auxillary_list']

        resourcefound = get_doc_resource_by_id(id)
        saved_resource = save_doc_feedback(id, feedbackdata)


        # Send async FormattingDeconstructionRequest
        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']

        message_publisher = MessagePublisher(BROKER_ADDR, EXCHANGE, logging.getLogger(consts.LOGGING_NAME))

        # Send FeedbackRequest
        feedback_req_msg = feedbackrequest(
            id_fb,
            resourcefound.document_file_path,
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

#
@ns.route('/<string:id>/metrics')
@ns.response(200, 'Document processing resource returned OK')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error')
class DocumentprocessingAPI(Resource):
    @ns.marshal_with(eTMFA_metrics_get)
    def get(self, id):
        """Returns metrics of document processed"""
        try:
            return get_doc_proc_metrics_by_id(id, full_mapping=True)
        except ValueError as error:
            return abort(404, 'No document resource exists for this id.')


@ns.route('/<string:id>/attributes')
@ns.response(200, 'Document processing resource returned OK')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error')
class DocumentprocessingAPI(Resource):
    @ns.marshal_with(eTMFA_attributes_get)
    def get(self, id):
        """Get the document processing object attributes"""
        try:
            return get_doc_processed_by_id(id, full_mapping=True)
        except ValueError as error:
            return abort(404, 'No document resource exists for this id.')


# Utility Functions

def build_processing_dir(ID):
    PROCESSING_DIR = get_root_dir()

    path = os.path.join(PROCESSING_DIR, str(ID) + "/")
    if not os.path.isdir(path):
        os.makedirs(path)

    return path