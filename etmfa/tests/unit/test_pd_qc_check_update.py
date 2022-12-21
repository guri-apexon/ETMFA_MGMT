import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("aidoc_id, parent_path, qc_approved_by, expected_status_cd, comments",
                         [("62166a73-bb80-441e-8ef7-4c09cce5a5d9", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/62166a73-bb80-441e-8ef7-4c09cce5a5d9", "1034911", HTTPStatus.OK, "Normal"),
                          # ("d3200e81-df2b-4dae-b987-e85b18db4817", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/d3200e81-df2b-4dae-b987-e85b18db4817", "1034911", HTTPStatus.OK, "Normal"),
                            ("0a1a6d7d-81c5-4da5-8625-0972aa1dbcae", "", "1034911", HTTPStatus.INTERNAL_SERVER_ERROR, "Missing parent path"),
                            ("", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/d3200e81-df2b-4dae-b987-e85b18db4817", "1034911", HTTPStatus.NOT_FOUND, "Missing aidoc id"),
                            ("0a1a6d7d-81c5-4da5-8625-0972aa1dbcae", "//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml/d3200e81-df2b-4dae-b987-e85b18db4817", "", HTTPStatus.INTERNAL_SERVER_ERROR, "Missing approved by"),
                            ("", "", "", HTTPStatus.NOT_FOUND, "Missing All"),

                          ])
def test_pd_qc_check_update(new_app_context,  aidoc_id, parent_path, qc_approved_by, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"aidoc_id": aidoc_id, "parent_path": parent_path, "qcApprovedBy": qc_approved_by}
    with client:
        logger.debug(f"test_pd_qc_check_update: Processing for unit test type [{comments}]: {id}]")
        response = client.post(f"/pd/api/v1/documents/pd_qc_check_update", json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd


