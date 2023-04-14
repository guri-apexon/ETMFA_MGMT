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
    
    def __init__(self, doc_id: str = '') -> None:
        super().__init__(doc_id)
        self.doc_id = doc_id

    def filter(self, record):
        record.doc_id = self.doc_id

        return True


def initialize_wf_logger(LOGSTASH_HOST, LOGSTASH_PORT, debug=True, module_name=Consts.LOGGING_WF,add_filter=True):
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    elkHandler = AsynchronousLogstashHandler(LOGSTASH_HOST,
                                             LOGSTASH_PORT,
                                             database_path=DB_FILE)
    elkHandler.setLevel(logging.INFO)
    logger.addHandler(elkHandler)

    if debug:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.DEBUG)
        consoleFormatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(doc_id)s] %(message)s')
        consoleHandler.setFormatter(consoleFormatter)
        logger.addHandler(consoleHandler)
    if add_filter:
         logger.addFilter(ContextFilter(''))
