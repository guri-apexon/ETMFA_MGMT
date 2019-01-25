import os, uuid, logging, requests, json

from flask_restplus import Namespace, Resource, fields, reqparse, abort
from flask import current_app, send_from_directory, request
import werkzeug

from ..api import api

from ...db import (
    get_root_dir,
    save_doc_translate,
    save_xliff_request,
    get_xliff_location_by_id,
    get_doc_translate_by_id,
    get_translated_xliff_location_by_id,
    get_metrics_dict,
    get_metadata_dict,
    upsert_metadata,
    add_supporting_doc,
    get_supporting_docs,
    delete_doctranslate_request,
    get_valid_lang_pairs,
    )

from ...consts import Consts as consts

from ...db.models.documenttranslate import DocumentTranslate

from ...messaging.messagepublisher import MessagePublisher
from ...messaging.models.formatting_deconstruction_request import FormattingDeconstructionRequest
from ...messaging.models.formatting_reconstruction_request import FormattingReconstructionRequest
from ...messaging.models.translation_xliff_update import TranslationXliffUpdate

from .serializers import *

ns = api.namespace('Document Translate', path='/v1/docTranslate', description='REST endpoints for document translation workflows.')

@ns.route('/')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.expect(document_translate_object_post)
    @ns.marshal_with(document_translate_object_get)
    @ns.response(201, 'Document translation resource created.')
    def post(self):
        """Create document translation REST object and returns document translation API object """

        # Generate processing dir
        args = document_translate_object_post.parse_args()

        # Generate ID
        _id = uuid.uuid4()
        path = build_processing_dir(_id)

        # get save path and output path
        processing_dir = build_processing_dir(_id)
        file = args['file']
        file_path = os.path.join(processing_dir, file.filename)

        # Save doc
        file.save(file_path)

        # Generate DTO and save
        get_lang_pairs_uri = current_app.config['GET_LANGUAGES_ADDR']
        saved_resource = save_doc_translate(args, _id, file_path, get_lang_pairs_uri)

        # Send async FormattingDeconstructionRequest
        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']

        msg_f = FormattingDeconstructionRequest(saved_resource['id'], file.filename, file_path,
            saved_resource['source_lang_short'], saved_resource['target_lang_short'])
        MessagePublisher(BROKER_ADDR, EXCHANGE, logging.getLogger(consts.LOGGING_NAME)).send_obj(msg_f)


        # Return response object 
        return get_doc_translate_by_id(_id, full_mapping=True)

@ns.route('/<string:id>/metadata')
@ns.response(404, 'Document translation resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.expect(metadata_post)
    @ns.marshal_with(metadata_post)
    @ns.response(201, 'Document translate resource returned OK')
    def post(self, id):
        """Create metadata dictionary object on the original translation resource."""
        md = request.json
        for m in md['metadata']:
            upsert_metadata(id, m['name'], m['val'])

        return get_metadata_dict(id)

    @ns.expect(metadata_post)
    @ns.marshal_with(metadata_post)
    @ns.response(201, 'Document translate resource retu rned OK')
    def patch(self, id):
        md = request.json
        for m in md['metadata']:
            upsert_metadata(id, m['name'], m['val'])
        
        return get_metadata_dict(id)

    @ns.marshal_with(metadata_post)
    @ns.response(201, 'Document translate resource retu rned OK')
    def get(self, id):
        return get_metadata_dict(id)

@ns.route('/<string:id>', endpoint='resource_get_ep')
@ns.response(404, 'Document translation resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.marshal_with(document_translate_object_get)
    @ns.response(200, 'Document translate resource returned OK')
    def get(self, id):
        """Get the document translation object without metadata. This includes any locations of processed documents"""
        try:
            return get_doc_translate_by_id(id, full_mapping=True)
        except ValueError as error:
            return abort(404, 'No document translation resource exists for this id.')

    @ns.marshal_with(document_translate_object_get)
    @ns.response(204, 'Marked Document translation resource as deleted.')
    def delete(self, id):
        """(Soft) Delete the document translation object and metadata."""

        return delete_doctranslate_request(id)


@ns.route('/<string:id>/formattedDoc', endpoint='formatted_doc_ep')
@ns.response(404, 'Document translation resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.response(200, 'Document returned OK', headers={'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'})
    # @api.header('Content-Type', 'octet-stream', required=True)
    def get(self, id):
        """Returns a file of the formatted, translated document if processing is complete."""
        
        resource = get_doc_translate_by_id(id)
        if resource == None or resource['is_processing'] or not resource['formatted_doc_path']:
            return abort(404, 'The formatted, translated document does not exist or has not yet finished processing.')

        if resource['is_processing'] == False and resource['edited_xliff_path'] and not resource['formatted_doc_path']:
            return abort(500, 'An error has occurred during document reconstruction. See error log.')

        path, file_name = os.path.split(resource['formatted_doc_path'])
        return send_from_directory(path, file_name)

@ns.route('/<string:id>/xliff', endpoint='xliff_ep')
@ns.response(200, 'Document translate resource returned OK')
@ns.response(404, 'Document translation resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.expect(document_translate_object_put)
    @ns.marshal_with(document_translate_object_get)
    def put(self, id):
        """
        Update REST object XLIFF and triggers another re-formatting
        """
        # Generate processing dir
        args = document_translate_object_put.parse_args()
        
        # Generate ID
        path = build_processing_dir(id)

        # get save path and output path
        processing_dir = build_processing_dir(id)
        file = args['file']
        file_path = os.path.join(processing_dir, file.filename)
        file.save(file_path)

        # Generate DTO and save
        saved_resource = save_xliff_request(id, file_path)

        # Send async FormattingDeconstructionRequest
        BROKER_ADDR = current_app.config['MESSAGE_BROKER_ADDR']
        EXCHANGE = current_app.config['MESSAGE_BROKER_EXCHANGE']


        message_publisher = MessagePublisher(BROKER_ADDR, EXCHANGE, logging.getLogger(consts.LOGGING_NAME))
        
        # Send FormattingReconstructionRequest
        reconstruction_req_msg = FormattingReconstructionRequest(
            id,
            file_path
        )
        message_publisher.send_obj(reconstruction_req_msg)

        # Send XLIFF updated msg
        if args['cache']:
            xliff_update_msg = TranslationXliffUpdate(id, file_path)
            message_publisher.send_obj(xliff_update_msg)

        return saved_resource

    def get(self, id):
        """Returns a file of the translated XLIFF file if processing is complete."""
        xliff_path = get_translated_xliff_location_by_id(id)
        if xliff_path == None:
            return abort(404, 'The XLIFF file does not exist for this resource.')
        path, file_name = os.path.split(xliff_path)

        return send_from_directory(path, file_name)


@ns.route('/<string:id>/metrics')
@ns.response(200, 'Document translate resource returned OK')
@ns.response(404, 'Document translation resource not found.')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.marshal_with(metrics)
    def get(self, id):
        """Returns a file of the translated XLIFF file if processing is complete."""
        metrics = get_metrics_dict(id)
        return metrics


@ns.route('/languagePairs')
class LanguagesAPI(Resource):
    @api.marshal_list_with(language_pair)
    def get(self):
        """Get a list of valid language pairs for translation input"""
        translation_microservice_addr = current_app.config['GET_LANGUAGES_ADDR']
        return get_valid_lang_pairs(translation_microservice_addr)


@ns.route('/<string:id>/supportingDocs')
@ns.response(500, 'Server error')
class DocumentTranslationAPI(Resource):
    @ns.expect(supporting_docs_post)
    @api.marshal_with(supporting_docs_get)
    @ns.response(201, 'Supporting document saved.')
    def post(self, id):
        """Upload any supporting document through the stages of external translation or formatting steps.
         This will assist in improving the translation and formatting efforts in the future. """

        # Generate processing dir
        args = supporting_docs_post.parse_args()
        path = build_processing_dir(id)

        # get save path and output path
        processing_dir = build_processing_dir(id)
        file = args['file']
        file_path = os.path.join(processing_dir, file.filename)

        # Save doc
        file.save(file_path)

        # Save to table
        return add_supporting_doc(id, file_path, args['description']), 201

    @api.marshal_list_with(supporting_docs_get)
    def get(self, id):
        """Get list of supporting documents saved. Get the list of documents that have been uploaded to save for archival and learning purposes."""

        return get_supporting_docs(id)['supporting_docs']



# Utility Functions

def build_processing_dir(ID):
    PROCESSING_DIR = get_root_dir()
    path = os.path.join(PROCESSING_DIR, str(ID) + "\\")

    if not os.path.isdir(path):
        os.makedirs(path)

    return path