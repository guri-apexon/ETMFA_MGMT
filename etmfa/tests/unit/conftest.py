import logging
import os
import pickle

import pytest
from etmfa.consts import Consts as consts
from etmfa.server import create_app

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

config_name = 'test'
test_file_details = [("SSR_1002-043", "a89de6a0-fc10-4964-9364-fa20962d44ef", "./etmfa/tests/data/FULL_finalattributes_dbdata.pkl")]
                                        
@pytest.fixture(scope="session", autouse=True)
def finalizer_complete_payload_cached():
    all_payload = dict()
    logger.info("Unit test documents cache process started")
    for protocol_num, aidoc_id, file_path in test_file_details:
        with open(file_path, "rb") as rf:
            full_finalattributes_dbdata_dict = pickle.load(rf)
            all_payload[protocol_num] = (aidoc_id, full_finalattributes_dbdata_dict)

    logger.info("Unit test documents cached successfully")
    return all_payload

@pytest.fixture(scope="session", autouse=True)
def new_app_context():
    _app = create_app(config_name)
    _app_context = _app.app_context()
    return _app, _app_context
