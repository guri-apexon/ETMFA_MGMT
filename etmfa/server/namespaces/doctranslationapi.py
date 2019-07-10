import os, uuid, logging, requests, json

from flask_restplus import Namespace, Resource, fields, reqparse, abort
from flask import current_app, send_from_directory, request
import werkzeug

from ..api import api

from ...db import (
    create_processing_config,
    get_processing_config,
    get_root_dir,
    save_doc_translate,
    save_doc_feedback,
    get_doc_resource_by_id,
    get_doc_translate_by_id,
    get_doc_processed_by_id,
    get_metrics_dict,
    get_metadata_dict,
    upsert_attributevalue,
    get_attributevalue,
    get_attribute_dict
    )

from ...consts import Consts as consts


from ...messaging.messagepublisher import MessagePublisher
from ...messaging.models.Triage_Request import TriageRequest
from ...messaging.models.feedback_request import feedbackrequest

from .serializers import *

ns = api.namespace('eTMFA', path='/v1/eTMFA', description='REST endpoints for eTMFA workflows.')

document_feedback = api.model('Document feedback definition', {
    #'processing_dir': fields.String(required=True, description='Processing directory for intermediate files.'),
    'id': fields.String(required=True, description='The unique identifier (UUID) of a document processing job.'),
    'feedback_source': fields.String(required=True, description='Feedback source for the processed document'),
    'customer': fields.String(required=True, description='Customer'),
    'protocol': fields.String(required=True, description='protocol'),
    'country': fields.String(required=True,  description='country'),
    'site': fields.String(required=True, description='site'),
    'document_class': fields.String(required=True, description='document class'),
    'document_date': fields.String(required=True, description='date string yyyymmdd'),
    'document_classification': fields.String(required=True, description='document classification'),
    'name': fields.String(required=True, description='name'),
    'language': fields.String(required=True, description='language'),
    'document_rejected': fields.String(required=True, description='document rejected'),
    #'attribute_auxillary_list': fields.List(fields.Nested(kv_pair_model)),
})

@ns.route('/')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.expect(eTMFA_object_post)
    @ns.marshal_with(eTMFA_object_get)
    @ns.response(201, 'Document translation resource created.')
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
        file_path  = os.path.join(processing_dir, file.filename)

        # Save doc
        file.save(file_path)

        customer = args['Customer']
        protocol = args['Protocol']
        country  = args['Country']
        site     = args['Site']
        document_class = args['Document_Class']
        tmf_ibr = args['TMF_IBR']
        blinded = args['Blinded']
        tmf_environment = args['TMF_Environment']
        received_date = args['Received_Date']
        site_personnel_list = args['site_personnel_list']
        priority = args['Priority']


        saved_resource = save_doc_translate(args, _id, file_path)
        #############
        print("checking if document written to database")
        resource = get_doc_resource_by_id(_id)
        if resource != None:
            print("record written to database", _id)
        else:
            print("record not written to database")
        ################################

        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']

        msg_f = TriageRequest(_id, file, file_path, customer, protocol, country, site, document_class,
                              tmf_ibr, blinded, tmf_environment, received_date, site_personnel_list, priority)
        #############
        print("checking if document written to database")
        resource = get_doc_resource_by_id(_id)
        if resource != None:
            print("record written to database : check before publishing", _id)
        else:
            print("record not written to database")
        ################################
        MessagePublisher(BROKER_ADDR, EXCHANGE, logging.getLogger(consts.LOGGING_NAME)).send_obj(msg_f)
        #############
        print("checking if document written to database")
        resource = get_doc_resource_by_id(_id)
        if resource != None:
            print("record written to database : checking after publishing", _id)
        else:
            print("record not written to database")
        ################################
        # Return response object
        return get_doc_translate_by_id(_id, full_mapping=True)

#@ns.route('/<string:id>/', endpoint = 'update_attribute_key')
@ns.route('/<string:id>/ update attribute/key')
@ns.response(404, 'Document translation resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.expect(metadata_post)
    @ns.marshal_with(eTMFA_attributes_get)
    @ns.response(201, 'Document translate resource returned OK')
    def patch(self, id):
        """"Update document attributes with key value """
        md = request.json
        for m in md['metadata']:
            #upsert_metadata(id, m['name'], m['val'])
            upsert_attributevalue(id, m['name'], m['val'])
        return get_attribute_dict(id)

#
# @ns.route('/<string:id>/get_attribute/key')
# @ns.response(404, 'Document translation resource not found.')
# @ns.response(500, 'Server error')
# class DocumentTranslationAPI(Resource):
#     @ns.expect(metadata_get)
#     @ns.marshal_with(metadata_post)
#     @ns.response(201, 'Document translate resource returned OK')
#     def get(self, id):
#         md = request.json
#         return get_attributevalue(id, md)
#



@ns.route('/<string:id>/ Document_processing_status')
@ns.response(404, 'Document Processing resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.marshal_with(eTMFA_object_get)
    @ns.response(200, 'Document procesing resource returned OK')
    def get(self, id):
        """Get document processing object status. This includes any locations of processed documents"""
        try:
            return get_doc_translate_by_id(id, full_mapping=True)
        except ValueError as error:
            return abort(404, 'No document processing resource exists for this id.')


#
@ns.route('/<string:id>/  Feedback Loop')
@ns.response(200, 'Document processing resource returned OK')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    #@ns.expect(document_processing_object_put)
    @ns.expect(document_feedback)
    @ns.marshal_with(document_processing_object_put_get)
    def put(self, id):
        """Feedback attributes to document processed"""
        #args = document_processing_object_put.parse_args()



        # format data for finalisation service to update IQVDocument
        feedbackdata = request.json
        id_fb = feedbackdata['id']
        feedback_source = feedbackdata['feedback_source']
        customer = feedbackdata['customer']
        protocol = feedbackdata['protocol']
        country = feedbackdata['country']
        site = feedbackdata['site']
        document_class = feedbackdata['document_class']
        document_date = feedbackdata['document_date']
        document_classification = feedbackdata['document_classification']
        name = feedbackdata['name']
        language = feedbackdata['language']
        document_rejected = feedbackdata['document_rejected']
        #attribute_auxillary_list = feedbackdata['attribute_auxillary_list']

        saved_resource = save_doc_feedback(id, feedbackdata)


        # Send async FormattingDeconstructionRequest
        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']


        message_publisher = MessagePublisher(BROKER_ADDR, EXCHANGE, logging.getLogger(consts.LOGGING_NAME))

        # Send FeedbackRequest
        feedback_req_msg = feedbackrequest(
            id_fb,
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
            document_rejected
            #attribute_auxillary_list
        )
        message_publisher.send_obj(feedback_req_msg)


        return saved_resource

#
@ns.route('/<string:id>/  Document_Metrics')
@ns.response(200, 'Document processing resource returned OK')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.marshal_with(metrics)
    def get(self, id):
        """Returns metrics of document processed"""
        metrics = get_metrics_dict(id)
        return metrics


@ns.route('/<string:id>/ Retrieve_document_attributes')
@ns.response(200, 'Document processing resource returned OK')
@ns.response(404, 'Document processing resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.marshal_with(eTMFA_attributes_get)
    def get(self, id):
        """Get the document processing object attributes"""
        try:
            #return get_doc_translate_by_id(id, full_mapping=True)
            return get_doc_processed_by_id(id, full_mapping=True)
        except ValueError as error:
            return abort(404, 'No document resource exists for this id.')

#
# @ns.route('/<string:id>/supportingDocs')
# @ns.response(500, 'Server error')
# class DocumentTranslationAPI(Resource):
#     @ns.expect(supporting_docs_post)
#     @api.marshal_with(supporting_docs_get)
#     @ns.response(201, 'Supporting document saved.')
#     def post(self, id):
#         """Upload any supporting document through the stages of external translation or formatting steps.
#          This will assist in improving the translation and formatting efforts in the future. """
#
#         # Generate processing dir
#         args = supporting_docs_post.parse_args()
#         path = build_processing_dir(id)
#
#         # get save path and output path
#         processing_dir = build_processing_dir(id)
#         file = args['file']
#         file_path = os.path.join(processing_dir, file.filename)
#
#         # Save doc
#         file.save(file_path)
#
#         # Save to table
#         return add_supporting_doc(id, file_path, args['description']), 201
#
#     @api.marshal_list_with(supporting_docs_get)
#     def get(self, id):
#         """Get list of supporting documents saved. Get the list of documents that have been uploaded to save for archival and learning purposes."""
#
#         return get_supporting_docs(id)['supporting_docs']



# Utility Functions

def build_processing_dir(ID):
    PROCESSING_DIR = get_root_dir()
    #PROCESSING_DIR = "C:\\Users\\q1019814\\Desktop\\TestingMS"

    path = os.path.join(PROCESSING_DIR, str(ID) + "/")
    print("printing path of document",path)
    if not os.path.isdir(path):
        os.makedirs(path)

    return path