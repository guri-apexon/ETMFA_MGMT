import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("userId, limit, page_num,expected_status_cd, comments",
                         [("test-user", "1", "0", HTTPStatus.OK, "Normal"),
                          ("test-user124", "1", "0", HTTPStatus.OK, "Non-Existent User"),
                          ]
                         )
def test_protocol_details(new_app_context, userId, limit, page_num, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        logger.debug(f"test_status_api: Processing for unit test type [{comments}]: {userId}]")
        response = client.get(f"/pd/api/v1/documents/get_protocol_details?"
                              f"userId={userId}&limit={limit}&page_num={page_num}",
                              headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
