import logging, sys, traceback, json
from flask import request, jsonify
from flask_restplus import abort

from logstash_async.handler import AsynchronousLogstashHandler
from .api import api

from ..consts import Consts as consts

@api.errorhandler
def handle_global_errors(error):
    logger = logging.getLogger(consts.LOGGING_NAME)

    try:
        payload = dict({'req': {
                    'headers': dict(request.headers),
                    'url': request.url,
                    'values': request.values,
                    'json': request.json,
                }
            })

        logger.exception(error, extra=payload)
    except Exception as e:
        logger.exception(e, exc_info=True)

    if isinstance(error, LookupError):
        # All LookupErrors throw 404s
        error.code = 404

    return {'message': str(error)}, getattr(error, 'code', 500)


# Configure
def configure_logging(app, log_level=logging.DEBUG):
    root = logging.getLogger(consts.LOGGING_NAME)
    root.setLevel(log_level)

    handler = AsynchronousLogstashHandler(app.config['LOGSTASH_HOST'], app.config['LOGSTASH_PORT'], database_path='logstash.db')
    root.addHandler(handler)

    return root