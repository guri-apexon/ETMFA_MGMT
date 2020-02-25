import logging
import os

from etmfa.consts import Consts
from etmfa.consts import Globals
from etmfa.server.api import api
from flask import request
from logstash_async.handler import AsynchronousLogstashHandler


@api.errorhandler
def handle_global_errors(error):
    # print("error raised globally",type(error))
    logger = logging.getLogger(Consts.LOGGING_NAME)

    try:
        payload = dict({'req': {
            'headers': dict(request.headers),
            'url': request.url,
            'values': request.values,
            'json': request.json,
        }
        })
        if not isinstance(error, LookupError):
            logger.exception(error, extra=payload)
    except Exception as e:
        logger.exception(e, exc_info=True)

    if isinstance(error, LookupError):
        # All LookupErrors throw 404s
        error.code = 404

    return {'message': str(error)}, getattr(error, 'code', 500)


DB_DIR = os.path.join("logs")
DB_FILE = os.path.join(DB_DIR, "logstash.db")


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.aidocid = None

        try:
            record.aidocid = Globals.FLASK_LOCAL.aidocid
        except (RuntimeError, AttributeError):
            # Not in Flask app context or missing attribute
            pass

        try:
            record.aidocid = Globals.GEVENT_LOCAL.aidocid
        except AttributeError:
            # Not in gevent context or missing attribute
            pass

        try:
            record.aidocid = Globals.THREAD_LOCAL.aidocid
        except AttributeError:
            pass

        return True


def initialize_logger(app, debug=True, module_name=Consts.LOGGING_NAME):
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    elkHandler = AsynchronousLogstashHandler(app.config['LOGSTASH_HOST'],
                                             app.config['LOGSTASH_PORT'],
                                             database_path=DB_FILE)
    elkHandler.setLevel(logging.INFO)
    logger.addHandler(elkHandler)

    if debug:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.DEBUG)
        consoleFormatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(aidocid)s] %(message)s')
        consoleHandler.setFormatter(consoleFormatter)
        logger.addHandler(consoleHandler)

    logger.addFilter(ContextFilter())
