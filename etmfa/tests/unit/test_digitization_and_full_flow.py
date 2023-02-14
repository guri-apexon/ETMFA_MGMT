import json
import requests
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("sourceFileName, versionNumber, protocolNumber, sponsor, sourceSystem, documentStatus, studyStatus, amendmentNumber, projectID, environment, indication, moleculeDevice, userId, file,workFlowName, expected_status_cd, comments",
                         [("test-protocol.pdf", "3.0", "SGN35-022", "Seattle Genetics, Inc.", "unit-test", "draft", "testStudy", "Y", "PD", "dev", "Randomized", "mol1", "test-user","//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/ae8190c4-3608-4629-8468-55b57a78243b/d5180c00025csp-FINAL-25Feb-clean (1).docx","full_flow", HTTPStatus.OK, "Normal"),
                         ("test-protocol.pdf", "3.0", "SGN35-022", "Seattle Genetics, Inc.", "unit-test", "draft", "", "Y", "PD", "dev", "Randomized", "mol1", "test-user", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/ae8190c4-3608-4629-8468-55b57a78243b/d5180c00025csp-FINAL-25Feb-clean (1).docx", "digitization", HTTPStatus.OK, "Normal"),
                         ("test-protocol.pdf", "3.0", "SGN35-022", "Seattle Genetics, Inc.", "unit-test", "draft", "", "Y", "PD", "dev", "Randomized", "mol1", "test-user", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/ae8190c4-3608-4629-8468-55b57a78243b/d5180c00025csp-FINAL-25Feb-clean (1).docx", "", HTTPStatus.OK, "Takes default full_flow"),
                         ("test-protocol.pdf", "3.0", "SGN35-022", "Seattle Genetics, Inc.", "unit-test", "draft", "", "Y", "PD", "dev", "Randomized", "mol1", "", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/ae8190c4-3608-4629-8468-55b57a78243b/d5180c00025csp-FINAL-25Feb-clean (1).docx", "digitization", HTTPStatus.OK, "Missing userId"),
                         ("", "3.0", "SGN35-022", "Seattle Genetics, Inc.", "unit-test", "draft", "", "Y", "PD", "dev", "Randomized", "mol1", "", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/ae8190c4-3608-4629-8468-55b57a78243b/d5180c00025csp-FINAL-25Feb-clean (1).docx", "", HTTPStatus.OK, "Missing sourceFileName")
                          ])
def test_document_post_api(new_app_context,  sourceFileName, versionNumber, protocolNumber, sponsor, sourceSystem,
                           documentStatus, studyStatus, amendmentNumber, projectID, environment, indication, moleculeDevice,
                           userId, file, workFlowName, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    filename = "test-protocol.pdf"
    # outer_tup_string = "file"

    # inner_tup = (filename, open(file, "rb"), "pdf")
    # final_list_tup = [(outer_tup_string, inner_tup)]

    input_dict = {"sourceFileName": sourceFileName, "versionNumber": versionNumber, "protocolNumber": protocolNumber,
                  "sponsor": sponsor, "sourceSystem": sourceSystem, "documentStatus": documentStatus, "amendmentNumber": amendmentNumber,
                  "projectID": projectID, "studyStatus": studyStatus, "environment": environment, "indication": indication,
                  "moleculeDevice": moleculeDevice, "userId": userId, "file": (open(file, 'rb'),filename), "workFlowName": workFlowName}
    with client:
        response = client.post(f"/pd/api/v1/documents/",
                                 data=input_dict, headers=Config.UNIT_TEST_HEADERS)

        assert response.status_code == expected_status_cd

