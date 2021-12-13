import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("id, expected_status_cd, comments",
                         [("9274fc1f-e645-4411-9b46-67d409e70108", HTTPStatus.OK, "Normal"),
                          ("0a1a6d7d-81c5-4da5-8625-0972aa1dbcae", HTTPStatus.NOT_FOUND, "Non exisitng aidoc_id")
                          ])
def test_status_api(new_app_context,  id,  expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"id": id}
    with client:
        logger.debug(f"test_status_api: Processing for unit test type [{comments}]: {id}]")
        response = client.get(f"/pd/api/v1/documents/{id}/status", json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
