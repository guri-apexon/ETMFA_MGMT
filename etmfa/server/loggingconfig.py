import logging
import os

from etmfa.consts import Consts
from etmfa.consts import Globals
from etmfa.server.api import api
from flask import request
from logstash_async.handler import AsynchronousLogstashHandler



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


def initialize_logger(log_stash_host, log_stash_port, debug=True, module_name=Consts.LOGGING_NAME,add_filter=True):
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    logger = logging.getLogger(module_name)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    elk_handler = AsynchronousLogstashHandler(log_stash_host,
                                             log_stash_port,
                                             database_path=DB_FILE)
    elk_handler.setLevel(logging.INFO)
    logger.addHandler(elk_handler)

    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(aidocid)s] %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    if add_filter:
        logger.addFilter(ContextFilter())


def initialize_api_logger(logstash_host, logstash_port, debug=True, module_name=Consts.LOGGING_API):
    """
    API logger configuration created to track API metrics with separate logger format
    """
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    logger = logging.getLogger(module_name)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    elk_handler = AsynchronousLogstashHandler(logstash_host,
                                             logstash_port,
                                             database_path=DB_FILE)
    elk_handler.setLevel(logging.INFO)
    logger.addHandler(elk_handler)

    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s PD [%(request_type)s-%(api_endpoint)s] [%(message)s]')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)