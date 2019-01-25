import os, logging, sys
from flask import Blueprint
from flask import Flask
from flask_cors import CORS, cross_origin
from flask_restplus import Api
from werkzeug.contrib.fixers import ProxyFix

# local imports
from .config import app_config
from ..db import init_db
from .loggingconfig import configure_logging

# api
from .namespaces.doctranslationapi import ns as doctranslation_namespace
from .namespaces.processingadminapi import ns as processing_namespace
from .api import api, specs_url

# messaging
from ..messaging import initialize_msg_listeners


dir_path = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__, instance_relative_config=True, instance_path=dir_path)
app.config.from_object(app_config['development'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def load_app_config(config_name):
    app.config.from_object(app_config[config_name])

    return app


def create_app(config_name, ssl_enabled=False):
    # Override 'Development' config when invoking server
    load_app_config(config_name)

    # register centralized logger
    logger = configure_logging(app)

    # register database instance
    init_db(app)

    # CORS
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    # register API
    api_blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(api_blueprint)
    app.register_blueprint(api_blueprint)

    # register API endpoints
    api.add_namespace(doctranslation_namespace)
    api.add_namespace(processing_namespace)

    # message listeners
    MSG_BROKER_ADDR = app.config['MESSAGE_BROKER_ADDR']
    EXCHANGE_NAME = app.config['MESSAGE_BROKER_EXCHANGE']
    initialize_msg_listeners(app, MSG_BROKER_ADDR, EXCHANGE_NAME, logger)

    # read X-Forwarded headers to retrieve current host
    app.wsgi_app = ProxyFix(app.wsgi_app)
    if (ssl_enabled):
        # https for swagger docs
        Api.specs_url = specs_url

    logging.info('Translation Management Service (TMS) application start-up: complete. SSL: {}'.format(str(ssl_enabled)))

    return app

