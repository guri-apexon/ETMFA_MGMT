from flask_restplus import Namespace, Resource, fields, reqparse, abort
from flask import Response

from ..api import api

ns = api.namespace('Health - Check', path='/health', description='Operations related to health check')

@ns.route('/')
class HealthprocessingAPI(Resource):
    def get(self):
        resp = Response('F5-UP', mimetype='text/html')
        resp.status_code = 200
        return resp

    def output_html(data, code, headers=None):
        resp = Response(data, mimetype='text/html', headers=headers)
        resp.status_code = code
        return resp