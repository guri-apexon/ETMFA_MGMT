from etmfa.db import create_processing_config
from etmfa.server.api import api
from flask import request
from flask_restplus import Resource, fields

ns = api.namespace('Admin - Processing', path='/admin/processing',
                   description='Operations related to application configuration')

processing = api.model('Processing definition', {
    'id': fields.Integer(required=True, description='Id for Processing directory. '),
    'processing_dir': fields.String(required=True, description='Processing directory for intermediate files.'),
})


@ns.route('/')
class ProcessingAPI(Resource):

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
