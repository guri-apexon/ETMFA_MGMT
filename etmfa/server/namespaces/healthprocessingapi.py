from flask import Flask, Blueprint, request, send_from_directory, render_template, url_for, jsonify
from flask_restplus import Namespace, Resource, fields, reqparse, abort
import werkzeug

from ...db import create_processing_config, get_processing_config

from ..api import api

ns = api.namespace('Health - Check', path='/health', description='Operations related to health check')

@ns.route('/')
class HealthprocessingAPI(Resource):
    #@ns.response(200, 'Success, Document processing API end points active')
    def get(self):
        #return 'Success - Document processing API end points active '
        return 200

