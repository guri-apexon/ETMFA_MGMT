import json
import logging
from http import HTTPStatus
import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("protocol_number, aidoc_id, source_system, expected_status_cd, comments",
                         [("P123", "cd62e2d4-c70b-4d49-88e4-4f623438bb14", "unit_test", HTTPStatus.OK, "Normal"),
                          ("", "cd62e2d4-c70b-4d49-88e4-4f623438bb14", "unit_test", HTTPStatus.NOT_FOUND, "Missing protocol"),
                          ("P123", "", "unit_test", HTTPStatus.NOT_FOUND, "Missing aidoc_id"),
                          ("", "", "unit_test", HTTPStatus.NOT_FOUND, "All missing")
                          ])
def test_normalized_soa(new_app_context, protocol_number, aidoc_id, source_system, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"protocolNumber": protocol_number, "id": aidoc_id, "sourceSystem": source_system}
    with client:
        logger.debug(f"test_normalized_soa: Processing for unit test type [{comments}]: [{protocol_number}, {aidoc_id}]")
        response = client.get("/pd/api/v1/documents/protocol_normalized_soa", json = input_dict, headers = Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['id'] == aidoc_id


