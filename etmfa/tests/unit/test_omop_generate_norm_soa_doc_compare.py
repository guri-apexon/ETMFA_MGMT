import json
import logging
from http import HTTPStatus
import pytest
import time
from etmfa.consts import Consts as consts
from etmfa.server.config import Config
import requests

logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("docId, workFlowName, expected_status_cd, comments",
                         [("2182c51f-fcee-4c1c-8a4c-dd9636ad0f91", "norm_soa" , HTTPStatus.OK, "Normal"),
                          ("", "norm_soa", HTTPStatus.NOT_FOUND, "Missing docId"),
                          ("a81dca57-c2e1-42f2-8ecd-61787d8f9d01", "",  HTTPStatus.NOT_FOUND, "Missing workFlowName"),
                          ("", "", HTTPStatus.NOT_FOUND, "All missing")
                          ])
def test_normalised_soa(new_app_context, docId, workFlowName ,expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"docId": docId, "workFlowName":workFlowName }
    
    with client:

        response = client.post("/pd/api/v1/documents/run_work_flow", json = input_dict, headers = Config.UNIT_TEST_HEADERS)       
        assert response.status_code == expected_status_cd


@pytest.mark.parametrize("docId,docIdToCompare,workFlowName, expected_status_cd, comments",
                         [("a81dca57-c2e1-42f2-8ecd-61787d8f9d01", "a713c98c-421c-4d31-ab03-d739276872ee" , "document_compare" , HTTPStatus.OK, "Normal"),
                          ("", "a713c98c-421c-4d31-ab03-d739276872ee",  "document_compare", HTTPStatus.NOT_FOUND, "Missing docId"),
                          ("a81dca57-c2e1-42f2-8ecd-61787d8f9d01","", "document_compare",  HTTPStatus.NOT_FOUND, "Missing docIdToCompare"),
                          ("",  "", "", HTTPStatus.NOT_FOUND, "All missing")
                          ])
def test_compare_document(new_app_context, docId, docIdToCompare, workFlowName, expected_status_cd, comments):

    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict = {"docId":docId , "docIdToCompare":docIdToCompare , "workFlowName":workFlowName}
    with client:
        response = client.post("/pd/api/v1/documents/run_work_flow", json = input_dict, headers = Config.UNIT_TEST_HEADERS)
        
        assert response.status_code == expected_status_cd