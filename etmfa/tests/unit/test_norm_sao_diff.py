import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("protocol_number, aidoc_id, compare_doc_id, source_system, expected_status_cd, comments",
                         [("AKB-6548-CI-0014", "edde6896-7eb1-4dfb-b0db-e40ea90daf1d", "9e8af4da-8989-4882-9875-806a21f2d438", "unit_test", HTTPStatus.OK, "Normal"),
                          ("", "edde6896-7eb1-4dfb-b0db-e40ea90daf1d", "9e8af4da-8989-4882-9875-806a21f2d438", "unit_test", HTTPStatus.NOT_FOUND, "Missing protocol"),
                          ("AKB-6548-CI-0014", "", "9e8af4da-8989-4882-9875-806a21f2d438", "unit_test", HTTPStatus.NOT_FOUND, "Missing aidoc_id"),
                          ("AKB-6548-CI-0014", "edde6896-7eb1-4dfb-b0db-e40ea90daf1d", "","unit_test", HTTPStatus.NOT_FOUND, "Missing compare_doc_id"),
                          ("", "", "", "unit_test", HTTPStatus.NOT_FOUND, "All missing"),
                          ("AKB-6548-CI-0014", "a89de6a0-fc10-4964-9364-fa20962d45f", "","unit_test", HTTPStatus.NOT_FOUND, "Non existing aidoc_id"),
                          ("AKB-6548-CI-0014", "a89de6a0-fc10-4964-9364-fa20962d44ef", "a89de6a0-fc10-4964-9364-fa20962d45g","unit_test", HTTPStatus.NOT_FOUND, "Non existing compare_doc_id"),
                          ("SSR_1002-04", "a89de6a0-fc10-4964-9364-fa20962d44ef", "a89de6a0-fc10-4964-9364-fa20962d45g","unit_test", HTTPStatus.NOT_FOUND, "Non existing protocol number"),
                          ])
def test_attr_soa(new_app_context, protocol_number, aidoc_id, compare_doc_id, source_system, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"protocolNumber": protocol_number, "baseDocId": aidoc_id, "compareDocId": compare_doc_id, "sourceSystem": source_system}
    with client:
        logger.debug(f"test_norm_soa_diff: Processing for unit test type [{comments}]: [{protocol_number}, {aidoc_id}, {compare_doc_id}]")
        response = client.get("/pd/api/v1/documents/norm_soa_compare", json = input_dict, headers = Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['normalizedSOADifference'] is not None
            
