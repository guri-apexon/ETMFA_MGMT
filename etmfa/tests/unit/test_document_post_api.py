import json
import requests
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config
from etmfa.db.db import db_context
from etmfa.db import WorkFlowStatus

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("sourceFileName, versionNumber, protocolNumber, sponsor, sourceSystem, documentStatus, studyStatus, amendmentNumber, projectID, environment, indication, moleculeDevice, userId, file, expected_status_cd, comments",
                         [("test-protocol.pdf", "1.0", "unit_test_protocol", "(CKD)Chong Kun Dang Pharm", "unit-test", "draft", "", "Y", "PD", "dev", "ABCC6 deficiency", "mol1", "test-user",
                          "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/ae8190c4-3608-4629-8468-55b57a78243b/d5180c00025csp-FINAL-25Feb-clean (1).docx", 
                         HTTPStatus.OK, "Normal")
                          ])
def test_document_post_api(new_app_context,  sourceFileName, versionNumber, protocolNumber, sponsor, sourceSystem,
                    documentStatus, studyStatus, amendmentNumber, projectID, environment, indication, moleculeDevice,
                    userId, file, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"sourceFileName": sourceFileName, "versionNumber": versionNumber, "protocolNumber": protocolNumber,
                  "sponsor": sponsor, "sourceSystem": sourceSystem, "documentStatus": documentStatus, "amendmentNumber": amendmentNumber,
                  "projectID": projectID, "studyStatus": studyStatus, "environment": environment, "indication": indication,
                  "moleculeDevice": moleculeDevice, "userId": userId, "file": (open(file, 'rb'),sourceFileName)}
    with client:
        response = client.post("/pd/api/v1/documents/",data=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd


@pytest.mark.parametrize("sourceFileName, versionNumber, protocolNumber, sponsor, sourceSystem, documentStatus, studyStatus, amendmentNumber, projectID, environment, indication, moleculeDevice, userId, file,duplicateCheck,expected_status_cd, comments",
                         [("test-protocol.pdf", "1.0", "unit_test_protocol", "(CKD)Chong Kun Dang Pharm", "unit-test", "draft", "", "Y", "PD", "dev", "ABCC6 deficiency", "mol1", "test-user", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/ae8190c4-3608-4629-8468-55b57a78243b/d5180c00025csp-FINAL-25Feb-clean (1).docx",False, HTTPStatus.OK, "Force Duplication"),
                         ("test-protocol.pdf", "1.0", "unit_test_protocol", "(CKD)Chong Kun Dang Pharm", "unit-test", "draft", "", "Y", "PD", "dev", "ABCC6 deficiency", "mol1", "test-user", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/ae8190c4-3608-4629-8468-55b57a78243b/d5180c00025csp-FINAL-25Feb-clean (1).docx",True, HTTPStatus.CONFLICT, "conflict expected on duplicate document")
                          ])
def test_document_post_api_duplication(new_app_context,  sourceFileName, versionNumber, protocolNumber, sponsor, sourceSystem,
                    documentStatus, studyStatus, amendmentNumber, projectID, environment, indication, moleculeDevice,
                    userId, file,duplicateCheck,expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"sourceFileName": sourceFileName, "versionNumber": versionNumber, "protocolNumber": protocolNumber,
                  "sponsor": sponsor, "sourceSystem": sourceSystem, "documentStatus": documentStatus, "amendmentNumber": amendmentNumber,
                  "projectID": projectID, "studyStatus": studyStatus, "environment": environment, "indication": indication,
                  "moleculeDevice": moleculeDevice, "userId": userId,"duplicateCheck":duplicateCheck,"file": (open(file, 'rb'),sourceFileName)}
    with client:
        response = client.post(f"/pd/api/v1/documents/", data=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
