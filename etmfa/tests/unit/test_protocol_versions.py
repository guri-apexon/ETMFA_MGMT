import ast
import json
import logging
from http import HTTPStatus
from etmfa.server.config import Config

import pytest
from etmfa.consts import Consts as consts

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

@pytest.mark.parametrize("api_endpoint, protocol_number, version_number, document_status, qc_status, source_system, expected_status_cd, expected_protocol_cnt, comments",
                         [("/pd/api/v1/documents/protocol_versions", "test1", "", "", "", "unit_test", HTTPStatus.OK, 1, "Only protocol number"),
                         ("/pd/api/v1/documents/protocol_versions", "test1", "", "", "qC_only", "unit_test", HTTPStatus.OK, 1, "QC_only status with case insenstive"),
                         ("/pd/api/v1/documents/protocol_versions", "test1", "", "", "AlL", "unit_test", HTTPStatus.OK, 1, "All status with case insensitive"),
                         ("/pd/api/v1/documents/protocol_versions", "test", "", "", "", "unit_test", HTTPStatus.NOT_FOUND, 0, "qc_only status"),
                         ("/pd/api/v1/documents/protocol_versions", "test", "", "", "qc_only", "unit_test", HTTPStatus.NOT_FOUND, 0, "qc_only status"),
                         ("/pd/api/v1/documents/protocol_versions", "test1", "", "", "  all ", "unit_test", HTTPStatus.OK, 1, "All status with extra spaces"),
                         ("/pd/api/v1/documents/protocol_versions", "test1", "", "all ", "  all ", "unit_test", HTTPStatus.OK, 1, "All qcStatus with all document status"),
                         ("/pd/api/v1/documents/protocol_versions", "test1", "", "final ", "  all ", "unit_test", HTTPStatus.OK, 1, "All qcStatus with draft document status"),
                         ("/pd/api/v1/documents/protocol_versions", "MLN0002SC-3030_POST3", "", "draft ", "  all ", "unit_test", HTTPStatus.OK, 1, "All qcStatus with final document status"),
                         ("/pd/api/v1/documents/protocol_versions", "XYZ", "", "", "all", "unit_test", HTTPStatus.NOT_FOUND, 0, "No results for the protocol"),
                         ("/pd/api/v1/documents/protocol_versions", "", "", "", "all", "unit_test", HTTPStatus.NOT_FOUND, 0, "Invalid protocol"),
                         ("/pd/api/v1/documents/mcra_latest_protocol", "test1", "", "", " ", "unit_test", HTTPStatus.OK, 1, "Only protocol number"),
                         ("/pd/api/v1/documents/mcra_latest_protocol", "test1", "", "", "qc_only", "unit_test", HTTPStatus.OK, 1, "QC_only status"),
                         ("/pd/api/v1/documents/mcra_latest_protocol", "test1", "", "", "all", "unit_test", HTTPStatus.OK, 1, "All status"),
                         ("/pd/api/v1/documents/mcra_latest_protocol", "SSR_M21_AKB-6548-CI-0014", "", "", "", "unit_test", HTTPStatus.NOT_FOUND, 0, "qc_only status"),
                         ("/pd/api/v1/documents/mcra_latest_protocol", "SSR_M21_AKB-6548-CI-0014", "", "", "qc_only", "unit_test", HTTPStatus.NOT_FOUND, 0, "qc_only status"),
                         ("/pd/api/v1/documents/mcra_latest_protocol", "test1", "", "", "QC_COMPLETED", "unit_test", HTTPStatus.OK, 1, "All status"),
                         ("/pd/api/v1/documents/mcra_latest_protocol", "XYZ", "", "", "all", "unit_test", HTTPStatus.NOT_FOUND, 0, "No results for the protocol"),
                         ("/pd/api/v1/documents/mcra_latest_protocol", "", "", "", "all", "unit_test", HTTPStatus.NOT_FOUND, 0, "Invalid protocol")
                          ])
def test_protocol_versions(new_app_context, api_endpoint, protocol_number, version_number, document_status, qc_status, source_system, expected_status_cd, expected_protocol_cnt, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"protocolNumber": protocol_number, "versionNumber": version_number, "documentStatus": document_status, \
                        "qcStatus": qc_status, "sourceSystem": source_system}

    with client:
        response = client.get(api_endpoint, json = input_dict, headers = Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd

        if response.status_code == HTTPStatus.OK:
            response_dict = json.loads(response.data)
            all_versions = ast.literal_eval(response_dict['allVersions'])
            assert len(all_versions) == expected_protocol_cnt


