import json
import logging
from http import HTTPStatus
import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("sponsor_name, expected_status_cd, comments",
                         [("GlaxoSmithKline", HTTPStatus.OK, "Normal"),
                          ("Invalid Sponsor", HTTPStatus.OK, "Invalid Sponsor Name")
                          ])
def test_get_confidence_matrix(new_app_context, sponsor_name, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"sponsorName": sponsor_name}
    with client:
        logger.debug(
            f"test_get_confidence_matrix: Processing for unit test type [{comments}]: [{sponsor_name}]")
        response = client.get("/pd/api/v1/documents/get_confidence_matrix",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd