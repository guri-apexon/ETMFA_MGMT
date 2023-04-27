import json
import logging
from http import HTTPStatus
import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config
from etmfa.server.namespaces.confidence_metric import ConfidenceMatrix,ConfidenceMatrixRunner,get_confidence_metric_stats
import time

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


CUSTOM_IDS=['d8219151-78af-4c80-9a52-2db43d961d2b']

def test_confidence_matrix():
    cm=ConfidenceMatrix()
    cm.add_custom_ids(CUSTOM_IDS)
    cm.run()

def test_confidence_matrix_runner():
    """
    test if multiple invocation of runners done only single instance runs
    """
    cmr=ConfidenceMatrixRunner()
    for _ in range(2):
        cmr.run(CUSTOM_IDS) 
        time.sleep(5)
        

@pytest.mark.parametrize("doc_id",CUSTOM_IDS)
def test_confidence_score_method(doc_id):
    cm=ConfidenceMatrix()
    cm.run()
    with cm.session_local() as session:
        confidence_score=get_confidence_metric_stats(session,[doc_id])
        assert confidence_score['confidence_score']!=0

@pytest.mark.parametrize("sponsor_name, expected_status_cd, comments",
                         [("GlaxoSmithKline", HTTPStatus.OK, "Normal"),
                          ("Invalid Sponsor", HTTPStatus.OK, "Invalid Sponsor Name")
                          ])
def test_get_confidence_matrix(new_app_context, sponsor_name, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"sponsorName": sponsor_name}
    with client:
        logger.debug(
            f"test_get_confidence_matrix: Processing for unit test type [{comments}]: [{sponsor_name}]")
        response = client.get("/pd/api/v1/documents/get_confidence_matrix",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd



