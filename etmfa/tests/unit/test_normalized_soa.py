import json
import logging
from http import HTTPStatus
import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("aidoc_id, source_system, operation_value, expected_status_cd, comments",
                         [("d4153421-2b47-4ec5-b21c-80d907d73227", "unit_test", "SOATable", HTTPStatus.OK, "Normal"),
                          ("d4153421-2b47-4ec5-b21c-80d907d73227", "unit_test", "normalizedSOA", HTTPStatus.OK, "Normal"),
                          ("d4153421-2b47-4ec5-b21c-80d907d73227", "unit_test", "",  HTTPStatus.NOT_FOUND, "Missing Operation Value"),
                          ("", "unit_test", "normalizedSOA", HTTPStatus.NOT_FOUND, "Missing aidoc_id"),
                          ("","unit_test", "", HTTPStatus.NOT_FOUND, "All missing")
                          ])
def test_normalized_soa(new_app_context, aidoc_id, source_system, operation_value, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"operationValue": operation_value , "id": aidoc_id, "sourceSystem": source_system}
    
    with client:
        logger.debug(f"test_normalized_soa: Processing for unit test type [{comments}]: [{operation_value}, {aidoc_id}]")
        response = client.get("/pd/api/v1/documents/protocol_normalized_soa", json = input_dict, headers = Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['id'] == aidoc_id
