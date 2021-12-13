import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize(
    "protocol_number, aidoc_id, approval_date, version_number, document_status, source_system, response_status, comments",
    [("test1", "9274fc1f-e645-4411-9b46-67d409e70108", "20140508", "1.0", "final", "unit_test", HTTPStatus.OK,
      "Normal"),
     ("", "9274fc1f-e645-4411-9b46-67d409e70108", "20140508", "1.0", "final", "unit_test", HTTPStatus.NOT_FOUND,
      "Missing protocol"),
     ("test1", "", "20140508", "1.0", "final", "unit_test", HTTPStatus.NOT_FOUND, "Missing aidoc_id"),
     ("test1", "9274fc1f-e645-4411-9b46-67d409e70108", "", "1.0", "final", "unit_test", HTTPStatus.OK,
      "Missing approval_date"),
     ("test1", "9274fc1f-e645-4411-9b46-67d409e70108", "20140508", "", "final", "unit_test", HTTPStatus.OK,
      "Missing version_no"),
     ("test1", "9274fc1f-e645-4411-9b46-67d409e70108", "20140508", "1.0", "", "unit_test", HTTPStatus.OK,
      "Missing document_status"),
     ("test1", "9274fc1f-e645-4411-9b46-67d409e70108", "20140508", "1.0", "final", "", HTTPStatus.OK,
      "Missing Source system"),
     ("", "", "", "", "", "", HTTPStatus.NOT_FOUND, "All missing")
     ])
def test_mcra_download_protocol(new_app_context, protocol_number, aidoc_id, approval_date, version_number,
                                document_status, source_system, response_status, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"protocolNumber": protocol_number, "id": aidoc_id, "approvalDate": approval_date,
                  "versionNumber": version_number,
                  "documentStatus": document_status, "sourceSystem": source_system}
    with client:
        logger.debug(
            f"test_mcra_download_protocol: Processing for unit test type [{comments}]: [{protocol_number}, {aidoc_id}, {version_number}]")
        response = client.get("/pd/api/v1/documents/mcra_download_protocols", json=input_dict,
                              headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == response_status
