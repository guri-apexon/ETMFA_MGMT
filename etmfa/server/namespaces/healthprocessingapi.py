"""Health Processing apis"""
from flask import Response
from flask_restplus import Resource
from etmfa.server.api import api

ns = api.namespace('Health - Check', path='/health',
                   description='Operations related to health check')


@ns.route('/')
class HealthprocessingAPI(Resource):
    """Helath Processing"""
    def get(self):
        """Get html page"""
        resp = Response('F5-UP', mimetype='text/html')
        resp.status_code = 200
        return resp

    def output_html(self, data, code, headers=None):
        """Output HTML"""
        resp = Response(data, mimetype='text/html', headers=headers)
        resp.status_code = code
        return resp
