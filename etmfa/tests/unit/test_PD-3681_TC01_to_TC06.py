import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config
import pytest_check as check

from etmfa.consts import Consts as consts
from etmfa.db import utils

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("version_date, approval_date, start_date, end_date, document_status, upload_date, qc_status, response_status, comments",
                        [('19000101', '19000101', '19000101', '20230101', 'final', '20210706', '', HTTPStatus.OK, "Normal"),
                        ('', '20000101', '', '', '', '', '',  HTTPStatus.OK, "Normal"),
                        ('', '', '', '', '', '20210706', '',  HTTPStatus.OK, "Normal"),
                        ('', '', '19000101', '20230101', '', '', '',  HTTPStatus.OK, "Normal"),
                        ('20200101', '', '', '', '', '', '', HTTPStatus.OK, "Normal"),
                        ('', '', '', '', 'final', '', '',  HTTPStatus.OK, "Normal"),
                        ('', '', '', '', 'final', '20210706', '', HTTPStatus.OK, "Normal"),
                        ('19000101', '19000101', '', '', 'final', '', '',  HTTPStatus.OK, "Normal"),
                        ('19000101', '19000101', '', '', '', '', '',  HTTPStatus.OK, "Normal"),
                        ('19000101', '19000101', '', '', 'final', '20210706', '', HTTPStatus.OK, "Normal"),
                        ('', '', '', '', '', '', 'QC_NOT_STARTED',  HTTPStatus.OK, "Normal")
                        ])
def test_get_protocols(new_app_context, version_date, approval_date, start_date, end_date, document_status, upload_date,
                                   qc_status, response_status, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"versionDate": version_date, "approvalDate": approval_date, "startDate":start_date, "end_date": end_date,
                  "documentStatus": document_status, "uploadDate": upload_date, "qc_status": qc_status}
    with client:
        logger.debug(
            f"test_get_protocols: Processing for unit test type [{comments}]: [{document_status}, {version_date}, {approval_date}]")
        response = client.get("/pd/api/v1/documents/get_protocols", json=input_dict,
                              headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == response_status