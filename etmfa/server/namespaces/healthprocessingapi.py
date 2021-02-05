from etmfa.server.api import api
from flask import Response
from flask_restplus import Resource

ns = api.namespace('Health - Check', path='/health', description='Operations related to health check')


@ns.route('/')
class HealthprocessingAPI(Resource):
    def get(self):
        resp = Response('ACCEPTING_REQUEST', mimetype='text/html')
        resp.status_code = 200
        return resp

    def output_html(data, code, headers=None):
        resp = Response(data, mimetype='text/html', headers=headers)
        resp.status_code = code
        return resp
