from flask import Flask, Blueprint, request, send_from_directory, render_template, url_for, jsonify
from flask_restplus import Namespace, Resource, fields, reqparse, abort
import werkzeug

from ...db import create_processing_config, get_processing_config

from ..api import api

ns = api.namespace('Admin - Processing', path='/admin/processing', description='Operations related to application configuration')

processing = api.model('Processing definition', {
    'processing_dir': fields.String(required=True, description='Processing directory for intermediate files.'),
})

@ns.route('/')
class ProcessingAPI(Resource):
    @api.marshal_with(processing)
    def get(self):
        """Get processing configuration"""
        return get_processing_config()

    @api.expect(processing)
    @api.marshal_with(processing)
    def post(self):
        """Create processing configuration data. Required only on initial application setup"""
        return create_processing_config(request.json)

    @api.expect(processing)
    @api.marshal_with(processing)
    def put(self):
        """Update processing configuration data"""
        return create_processing_config(request.json)

