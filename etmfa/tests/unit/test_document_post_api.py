import json
import requests
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

dev_endpoint = "http://ca2spdml01q:9001"
@pytest.mark.parametrize("sourceFileName, versionNumber, protocolNumber, sponsor, sourceSystem, documentStatus, studyStatus, amendmentNumber, projectID, environment, indication, moleculeDevice, userId, file, expected_status_cd, comments",
                         [("test-protocol.pdf", "1.0", "unit_test_protocol", "(CKD)Chong Kun Dang Pharm", "unit-test", "draft", "", "Y", "PD", "dev", "ABCC6 deficiency", "mol1", "test-user", r"./etmfa/tests/data/test-protocol.pdf", HTTPStatus.OK, "Normal")
                          ])
def test_document_post_api(new_app_context,  sourceFileName, versionNumber, protocolNumber, sponsor, sourceSystem,
                    documentStatus, studyStatus, amendmentNumber, projectID, environment, indication, moleculeDevice,
                    userId, file, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    filename = "test-protocol.pdf"
    outer_tup_string = "file"

    inner_tup = (filename, open(file, "rb"), "pdf")
    final_list_tup = [(outer_tup_string, inner_tup)]

    input_dict = {"sourceFileName": sourceFileName, "versionNumber": versionNumber, "protocolNumber": protocolNumber,
                  "sponsor": sponsor, "sourceSystem": sourceSystem, "documentStatus": documentStatus, "amendmentNumber": amendmentNumber,
                  "projectID": projectID, "studyStatus": studyStatus, "environment": environment, "indication": indication,
                  "moleculeDevice": moleculeDevice, "userId": userId, "file": file}
    with client:
        logger.debug(f"test_document_post_api: Processing for unit test type [{comments}]: {id}]")
        response = requests.post(f"{dev_endpoint}/pd/api/v1/documents/", files=final_list_tup, data=input_dict, headers=Config.UNIT_TEST_HEADERS)

        assert response.status_code == expected_status_cd

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.content)['id'] is not None


