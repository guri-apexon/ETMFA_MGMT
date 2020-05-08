import logging
import os
from pathlib import Path
import sys

from etmfa.consts import Consts
from etmfa.db import init_db
# messaging
from etmfa.messaging import initialize_msg_listeners
from etmfa.server.api import api, specs_url
# local imports
from etmfa.server.config import app_config
from etmfa.server.loggingconfig import initialize_logger
from etmfa.server.config import Config
# api
from etmfa.server.namespaces.docprocessingapi import ns as docprocessing_namespace
from etmfa.server.namespaces.healthprocessingapi import ns as health_namespace
from flask import Blueprint, request, g
from flask import Flask
from flask_cors import CORS
from flask_restplus import Api
from werkzeug.contrib.fixers import ProxyFix

dir_path = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__, instance_relative_config=True, instance_path=dir_path)
app.config.from_object(app_config['development'])
app.config['RESTPLUS_MASK_SWAGGER'] = False
app.config['ERROR_404_HELP'] = False


def load_app_config(config_name):
    app.config.from_object(app_config[config_name])

    return app


def create_app(config_name, ssl_enabled=False):
    # Override 'Development' config when invoking server
    load_app_config(config_name)

    # register centralized logger
    initialize_logger(app)
    logger = logging.getLogger(Consts.LOGGING_NAME)

    if Path(Config.DFS_UPLOAD_FOLDER).exists():
        logger.info('reading dfs path {}'.format(Config.DFS_UPLOAD_FOLDER))
    else:
        logger.error(f'Error while reading dfs folder path.')
        sys.exit(f'Error while reading dfs folder path.')

        # register database instance
    init_db(app)

    # CORS
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    # register API
    api_blueprint = Blueprint('api', __name__, url_prefix='/etmfa/api')

    @api_blueprint.before_request
    def saveAidocId():
        body = request.get_json()
        if body and body.get("id"):
            g.aidocid = body.get("id")
        else:
            g.aidocid = request.args.get("id")

    api.init_app(api_blueprint)
    app.register_blueprint(api_blueprint)

    # register API endpoints
    api.add_namespace(docprocessing_namespace)

    # message listeners
    MSG_BROKER_ADDR = app.config['MESSAGE_BROKER_ADDR']
    EXCHANGE_NAME = app.config['MESSAGE_BROKER_EXCHANGE']
    initialize_msg_listeners(app, MSG_BROKER_ADDR, EXCHANGE_NAME, logger)

    # read X-Forwarded headers to retrieve current host
    app.wsgi_app = ProxyFix(app.wsgi_app)
    if ssl_enabled:
        # https for swagger docs
        Api.specs_url = specs_url

    logger.info('eTMFA application start-up: complete. SSL: {}'.format(str(ssl_enabled)))

    return app
