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

@pytest.mark.parametrize("protocol_number, version_number, approval_date, aidoc_id, document_status, response_status, comments", 
                    [("0212_D361BC00001", '1', '20210404', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', 'final', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '', '', '', '', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '', '', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', '', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '1', '', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', '', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '', '20210404', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', '', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '1', '20210404', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', '', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '1', '', '', '', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '', '20210404', '', '', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '1', '20210404', '', '', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '1', '20210404', '', 'final', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '1', '20210404', '', 'draft', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '1', '20210404', '', 'all', HTTPStatus.OK, "Normal"),
                    ("0212_D361BC00001", '1', '20210404', '', '', HTTPStatus.OK, "Normal"),
                    ])
def test_dynamic_rules(new_app_context, protocol_number, version_number, approval_date, aidoc_id, document_status, response_status, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"protocolNumber": protocol_number, "versionNumber":version_number, "approvalDate": approval_date, "aidoc_id":aidoc_id, "documentStatus": document_status}
    with client:
        logger.debug(
            f"test_get_protocols: Processing for unit test type [{comments}]: [{document_status}, {aidoc_id}, {approval_date}]")
        response = client.get("/pd/api/v1/documents/get_protocols", json=input_dict,
                              headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == response_status
