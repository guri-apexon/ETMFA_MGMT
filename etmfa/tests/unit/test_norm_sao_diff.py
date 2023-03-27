import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("protocol_number, aidoc_id, compare_doc_id, source_system, expected_status_cd, comments",
                         [("pb.b003f92c-7e72-4db8-a32d-e319265a302e", "cc8f4d17-58db-4139-90c4-98be0c896766", "375e9e2e-b90f-4832-89c8-d71b0b569140", "unit_test", HTTPStatus.OK, "Normal"),
                          ("", "0a1a6d7d-81c5-4da5-8625-0972aa1dbcae", "06c65de2-e9df-442c-a7c0-399675640475", "unit_test", HTTPStatus.NOT_FOUND, "Missing protocol"),
                          ("test_AKB-6548-CI-0014", "", "06c65de2-e9df-442c-a7c0-399675640475", "unit_test", HTTPStatus.NOT_FOUND, "Missing aidoc_id"),
                          ("test_AKB-6548-CI-0014", "0a1a6d7d-81c5-4da5-8625-0972aa1dbcae", "","unit_test", HTTPStatus.NOT_FOUND, "Missing compare_doc_id"),
                          ("", "", "", "unit_test", HTTPStatus.NOT_FOUND, "All missing"),
                          ("test_AKB-6548-CI-0014", "a89de6a0-fc10-4964-9364-fa20962d45f", "","unit_test", HTTPStatus.NOT_FOUND, "Non existing aidoc_id"),
                          ("test_AKB-6548-CI-0014", "a89de6a0-fc10-4964-9364-fa20962d44ef", "a89de6a0-fc10-4964-9364-fa20962d45g","unit_test", HTTPStatus.NOT_FOUND, "Non existing compare_doc_id"),
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
            
