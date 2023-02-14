import json
import requests
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("docId, workFlowName, expected_status_cd, comments",
                         [("2182c51f-fcee-4c1c-8a4c-dd9636ad0f91", "meta_extraction", HTTPStatus.OK, "Normal"),
                          ("", "meta_extraction", HTTPStatus.NOT_FOUND, "Missing docId"),
                          ("a81dca57-c2e1-42f2-8ecd-61787d8f9d01", "",  HTTPStatus.NOT_FOUND, "Missing workFlowName"),
                          ("", "", HTTPStatus.NOT_FOUND, "All missing")])
def test_meta_extraction(new_app_context, docId, workFlowName,
                            expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"docId":docId, "workFlowName":workFlowName}
    with client:
        logger.debug(
            f"test_meta_extraction: Processing for unit test type [{comments}]: {docId}]")
        response = client.post("/pd/api/v1/documents/run_work_flow",
                                  data=input_dict, headers=Config.UNIT_TEST_HEADERS)

        assert response.status_code == expected_status_cd
