import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("protocol_number, aidoc_id, source_system, expected_status_cd, comments",
                         [("p2022", "00064316-897c-4d7e-927b-7127b669b01a", "unit_test", HTTPStatus.OK, "Normal"),
                          ("", "a89de6a0-fc10-4964-9364-fa20962d44ef", "unit_test", HTTPStatus.NOT_FOUND, "Missing protocol"),
                          ("SSR_1002-043", "", "unit_test", HTTPStatus.NOT_FOUND, "Missing aidoc_id"),
                          ("", "", "unit_test", HTTPStatus.NOT_FOUND, "All missing"),
                          ("SSR_1002-043", "a89de6a0-fc10-4964-9364-fa20962d44e", "unit_test", HTTPStatus.NOT_FOUND, "Non existing aidoc_id"),
                          ("SSR_1002-04", "a89de6a0-fc10-4964-9364-fa20962d44ef", "unit_test", HTTPStatus.NOT_FOUND, "Non existing protocol number"),
                          ])
def test_attr_soa(new_app_context, protocol_number, aidoc_id, source_system, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"protocolNumber": protocol_number, "id": aidoc_id, "sourceSystem": source_system}
    with client:
        logger.debug(f"test_attr_soa: Processing for unit test type [{comments}]: [{protocol_number}, {aidoc_id}]")
        response = client.get("/pd/api/v1/documents/protocol_attributes_soa", json = input_dict, headers = Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['id'] == aidoc_id
