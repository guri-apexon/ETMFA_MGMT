import pytest
import logging
from http import HTTPStatus

from etmfa.consts import Consts as consts
from etmfa.server.config import Config


# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("op, response_status, comments",
                         [("enable_cdc",  HTTPStatus.OK, "normal"),
                          ("ecdc",  HTTPStatus.BAD_REQUEST, "Bad request")])
def test_enable_cdc(new_app_context, op, response_status, comments):
    """
        Tests CDC.
    """
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        response = client.post("/pd/api/v1/documents/cdc?op="+op, headers=Config.UNIT_TEST_HEADERS, )
        assert response.status_code == response_status

@pytest.mark.parametrize("id, response_status, comments",
                         [("c2b994a4-e1ae-473e-a464-aa55e672c6c6",  HTTPStatus.OK, "normal"),
                          ("enable_cdc",  HTTPStatus.NOT_FOUND, "normal")])
def test_cdc_get_status(new_app_context, id, response_status, comments):
    """
        Tests CDC Status.
    """
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        response = client.get("/pd/api/v1/documents/cdc_status/"+id+"/", headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == response_status
