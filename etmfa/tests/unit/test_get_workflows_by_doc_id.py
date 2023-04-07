import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("doc_id, days, wf_num, expected_status_cd, comments",
                         [("02cb4d51-273c-4d85-b2d4-495454133b36", 90, 5, HTTPStatus.OK
                           , "Normal"),
                          ("02cb4d51-273c-4d85-b2d4-495454133b36", 180, 12, HTTPStatus.OK, "Normal")
                          ])
def test_get_workflows_by_docId(new_app_context, doc_id, days, wf_num, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    with client:
        logger.debug(
            f"get_workflows_by_doc_id: Processing for unit test type [{comments}]: [{doc_id}]")
        response = client.get(
            f"/pd/api/v1/documents/get_workflows_by_doc_id?"
            f"doc_id={doc_id}&days={days}&wf_num={wf_num}",
            headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
