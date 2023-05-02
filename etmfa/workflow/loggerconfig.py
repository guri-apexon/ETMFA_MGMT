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
    
    def __init__(self, doc_id) -> None:
        super().__init__(doc_id)
        self.doc_id = doc_id

    def filter(self, record):
        record.doc_id = self.doc_id

        return True


def initialize_wf_logger(logstash_host, logstash_port, debug=True, module_name=Consts.LOGGING_WF,add_filter=True):
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
        console_formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(doc_id)s] %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    if add_filter:
         logger.addFilter(ContextFilter(''))
