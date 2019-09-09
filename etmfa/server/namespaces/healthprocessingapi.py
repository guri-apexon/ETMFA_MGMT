from flask_restplus import Namespace, Resource, fields, reqparse, abort


from ..api import api

ns = api.namespace('Health - Check', path='/health', description='Operations related to health check')

@ns.route('/')
class HealthprocessingAPI(Resource):
    def get(self):
        return 200

