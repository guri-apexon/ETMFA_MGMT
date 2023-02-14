import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("docId, expected_status_cd, comments",
                         [("2182c51f-fcee-4c1c-8a4c-dd9636ad0f91", HTTPStatus.OK, "Normal"),
                          ("0a1a6d7d-81c5-4da5-8625-0972aa1dbce", HTTPStatus.NOT_FOUND, "Non exisitng aidoc_id"),
                          ("", HTTPStatus.NOT_FOUND, "Missing aidoc_id")
                          ])
def test_status_api(new_app_context,  docId,  expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        logger.debug(f"test_status_api: Processing for unit test type [{comments}]: {docId}]")
        response = client.get(f"/pd/api/v1/documents/{docId}/status",headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
