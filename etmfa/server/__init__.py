import logging
import os
from pathlib import Path
import sys

from etmfa.consts import Consts
from etmfa.db import init_db
# messaging
from etmfa.server.api import api, specs_url
from etmfa.server.config import Config, app_config
from .loggingconfig import initialize_logger, initialize_api_logger
from etmfa.server.namespaces.confidence_metric import  ConfidenceMatrixRunner
# api
from etmfa.server.namespaces.docprocessingapi import ns as docprocessing_namespace
from etmfa.server.namespaces.healthprocessingapi import ns as health_namespace
from etmfa.server.namespaces.cptconfigapi import ns as config_namespace
from etmfa.server.namespaces.pd_email_notification import ns as pd_notifications
from flask import Blueprint, request, g
from flask import Flask
from flask_cors import CORS
from flask_restplus import Api
from werkzeug.contrib.fixers import ProxyFix
from etmfa_core.postgres_db_schema import create_schemas
from microservices import ElasticIngestionRunner,EmailNotificationRunner
from etmfa.workflow import  WorkFlowClient,WorkFlowRunner
from etmfa.consts import Consts as consts
from ..utilities.user_metrics import create_or_update_user_metrics

dir_path = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__, instance_relative_config=True, instance_path=dir_path)
app.config.from_object(app_config['development'])
app.config['RESTPLUS_MASK_SWAGGER'] = False
app.config['ERROR_404_HELP'] = False
CORS(app)

api_logger = logging.getLogger(consts.LOGGING_API)


@app.after_request
def after_request_callback(response):
    """ TO get user and API metrics """
    extra_val = {'request_type': f"{request.method}",
                 'api_endpoint': f"{request.path}"}
    if response.status_code != 200:
        api_logger.error(msg="API Metrics exception",
                         extra=extra_val)
    else:
        api_logger.info(msg="API Metrics",
                        extra=extra_val)

    if request.path in ('/pd/api/cpt_data/',
                        '/pd/api/cpt_data/get_section_data_configurable_parameter') and str(
        request.args.get('toc', '')) == '1' and not request.method == "OPTIONS":
        user_id = request.args.get('user_id')
        aidoc_id = request.args.get('aidoc_id')
        # User metric protocol parameter
        create_or_update_user_metrics(user_id, aidoc_id)
    return response


def load_app_config(config_name):
    app.config.from_object(app_config[config_name])

    return app


def start_workflow_runner(logger):
    # start workflow runner
    wfr_inst = WorkFlowRunner(app.config)
    wfr_inst.start_process()
    # wf client is singleton class only once connection created.
    WorkFlowClient(app.config["ZMQ_PORT"], logger)


def start_runners():
    es = ElasticIngestionRunner()
    es.start()
    em= EmailNotificationRunner()
    em.start()
    cfr=ConfidenceMatrixRunner()
    cfr.start()


def create_app(config_name, ssl_enabled=False):
    # Override 'Development' config when invoking server
    load_app_config(config_name)
    logger = logging.getLogger(Consts.LOGGING_NAME)
    if app.config['WORK_FLOW_RUNNER']:
        create_schemas(app.config['SQLALCHEMY_DATABASE_URI'])
        start_workflow_runner(logger)
        start_runners()
    # register centralized logger
    initialize_logger(app.config['LOGSTASH_HOST'], app.config['LOGSTASH_PORT'])
    initialize_api_logger(app.config['LOGSTASH_HOST'], app.config['LOGSTASH_PORT'])

    if config_name == 'test':
        logger.info(
            f'Target folder check not required for config_name: {config_name}')
    elif Path(Config.DFS_UPLOAD_FOLDER).exists():
        logger.info('reading dfs path {}'.format(Config.DFS_UPLOAD_FOLDER))
    else:
        logger.error(
            f'DFS upload folder does not exist. Please make sure that upload folder is correctly set. Exiting management service.')
        sys.exit(
            f'DFS upload folder does not exist. Please make sure that upload folder is correctly set. Exiting management service.')

    # register database instance
    init_db(app)

    # CORS
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    # register API
    api_blueprint = Blueprint('api', __name__, url_prefix='/pd/api')

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

    # read X-Forwarded headers to retrieve current host
    app.wsgi_app = ProxyFix(app.wsgi_app)
    if ssl_enabled:
        # https for swagger docs
        Api.specs_url = specs_url

    logger.info(
        'PD application start-up: complete. SSL: {}'.format(str(ssl_enabled)))

    return app
