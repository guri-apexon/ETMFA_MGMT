import json
import logging
from http import HTTPStatus
import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

logger = logging.getLogger(consts.LOGGING_NAME)

"""
Get Normalized SOA data
"""
# get normalized soa data
@pytest.mark.parametrize("aidoc_id, source_system, operation_value, expected_status_cd, comments",
                         [("d4153421-2b47-4ec5-b21c-80d907d73227", "unit_test", "SOATable", HTTPStatus.OK, "Normal"),
                          ("d4153421-2b47-4ec5-b21c-80d907d73227", "unit_test", "normalizedSOA", HTTPStatus.OK, "Normal"),
                          ("d4153421-2b47-4ec5-b21c-80d907d73227", "unit_test", "",  HTTPStatus.NOT_FOUND, "Missing Operation Value"),
                          ("", "unit_test", "normalizedSOA", HTTPStatus.NOT_FOUND, "Missing aidoc_id"),
                          ("","unit_test", "", HTTPStatus.NOT_FOUND, "All missing")
                          ])
def test_normalized_soa(new_app_context, aidoc_id, source_system, operation_value, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"operationValue": operation_value , "id": aidoc_id, "sourceSystem": source_system}
    
    with client:
        logger.debug(f"test_normalized_soa: Processing for unit test type [{comments}]: [{operation_value}, {aidoc_id}]")
        response = client.get("/pd/api/v1/documents/protocol_normalized_soa", json = input_dict, headers = Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['id'] == aidoc_id



# Update, Create, Delete Operations for normalized soa
@pytest.mark.parametrize("update_request, expected_status_cd, comments",
                         [
                            ({"operation": "update", "sub_type": "update_cell", "table_props": {"doc_id":"", "table_roi_id": "ed04448a-9c17-4a64-8741-36a6934956cc", "table_row_index": "11", "table_column_index": "3", "value": "Continuous", "timepoint": "" } }, HTTPStatus.OK, "Normal"),
                            ({}, HTTPStatus.BAD_REQUEST, "Missing dictionary data"),
                            ({ "operation": "update", "sub_type": "update_study_procedure", "table_props": { "doc_id": "", "table_roi_id": "8715826c-6480-4162-9e83-f54ddf479d70", "table_row_index": "6", "table_column_index": "", "timepoint": "", "value": "Hepatitis and HIV screen" } }, HTTPStatus.OK, "Normal"),
                            ({ "operation": "update", "sub_type": "update_study_visit", "table_props": { "doc_id": "", "table_roi_id": "5af15495-9d79-4887-a396-29c2dc230c45", "table_row_index": "", "table_column_index": "2", "timepoint": "day_timepoint", "value": "1" } }, HTTPStatus.OK, "Normal"),
                            ({ "operation": "add", "sub_type": "add_row", "table_props": { "doc_id": "d2992899-24d4-4f51-a5e0-a8d8bfce4ace", "table_roi_id": "ed04448a-9c17-4a64-8741-36a6934956cc", "table_row_index": "5", "study_procedure": { "table_column_index": "0", "value": "vitals" }, "row_props": [{ "table_column_index": "2", "value": "10" }, { "table_column_index": "3", "value": "11" } ] } }, HTTPStatus.OK, "Normal"),
                            ({"operation": "delete", "sub_type": "delete_row", "table_props": { "table_roi_id": "ed04448a-9c17-4a64-8741-36a6934956cc", "table_row_index": "5" } }, HTTPStatus.OK, "Normal"),
                            ({ "operation": "add", "sub_type": "add_column", "table_props": { "doc_id": "d2992899-24d4-4f51-a5e0-a8d8bfce4ace", "table_roi_id": "ed04448a-9c17-4a64-8741-36a6934956cc", "table_column_index": "3", "study_visit": [{ "table_row_index": "0", "timepoint": "cycle_timepoint", "value": "m1" }, { "table_row_index": "0", "timepoint": "visit_timepoint", "value": "e1" }], "row_props": [{ "table_row_index": "2", "value": "10" }, { "table_row_index": "3", "value": "11" } ] } }, HTTPStatus.OK, "Normal"),
                            ({"operation": "delete", "sub_type": "delete_column", "table_props": { "table_roi_id": "ed04448a-9c17-4a64-8741-36a6934956cc", "table_column_index": "3" } }, HTTPStatus.OK, "Normal"),
                            ({"operation": "update", "sub_type": "add_cell", "table_props": {"doc_id":"f92f9d8b-8d2b-4d1d-a933-29fc6efe0932", "table_roi_id": "f47decb8-be69-44ee-ae51-f1dce73ab87f", "table_row_index": "37", "table_column_index": "6", "value": "Continuous", "timepoint": "" } }, HTTPStatus.OK, "Normal"),
                          ])
def test_normalized_soa_operations(new_app_context, update_request, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    
    with client:
        logger.debug(f"test_normalized_soa_update: Processing for unit test type.{comments}")
        response = client.post("/pd/api/v1/documents/protocol_normalized_soa_operations", json = update_request, headers = Config.UNIT_TEST_HEADERS)
        if expected_status_cd == response.status_code:
            assert response.status_code == expected_status_cd



