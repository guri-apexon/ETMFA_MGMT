import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


UNAUTHORIZED_MSG = "Credential validation: Authentication failed for given username and password"
DELETE_BASE_PATH = "/pd/api/v1/documents/delete_meta_data"
CONTENT_TYPE = "application/json"
DOC_ID = "00102246-ef34-4253-a03a-d9f1a045e19e"
DELETE_FIELD = "deleteField"
ADD_FIELD = "addField"
ADD_ATTRIBUTES = "addAttributes"
METADATA = "metadata"
METAPARAM = "metaparam"
DELETE_ATTRIBUTE = "deleteAttribute"

input_dict = {
    "op": '',
    "aidocId": '',
    "fieldName": ''
}
"""
Test cases for delete data if exists
"""
@pytest.mark.order(1)
@pytest.mark.parametrize("op, aidoc_id, field_name, attribute_names, soft_delete, expected_status_cd, comments",
                         [(DELETE_FIELD, "", "default_field", [], False, HTTPStatus.OK, "delete default field if there only for consistency"),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb.cc.dd.ee", [], False, HTTPStatus.OK, "delete field if there only for consistency"),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb.cc.dd.ee", [], False, HTTPStatus.OK, "at level 6"),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb.cc.dd", [], False, HTTPStatus.OK, "at level 5"),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb.cc", [], False, HTTPStatus.OK, "at level 4"),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb", [], False, HTTPStatus.OK, "at level 3"),
                          (DELETE_FIELD, DOC_ID, "test_info.aa", [], False, HTTPStatus.OK, "at level 2"),
                          (DELETE_FIELD, DOC_ID, "test_info", [],False, HTTPStatus.OK, "at level 1"),
                        ])
                         
def test_delete_metadata_start(new_app_context, op, aidoc_id, field_name, attribute_names, soft_delete, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name,
        "attribute_name": attribute_names,
        "softDelete":soft_delete,
    })

    with client:
        logger.debug(
            f"test_delete_metadata: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}, {attribute_names}]")
        response = client.delete(DELETE_BASE_PATH,
                                 json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd


"""
Test cases for add metadata
"""
@pytest.mark.order(2)
@pytest.mark.parametrize("op, aidoc_id, field_name, attributes, expected_status_cd, comments,valid",
                            [(ADD_FIELD, DOC_ID, "test_info", [],  HTTPStatus.OK, "at level 1", True),
                             (ADD_FIELD, DOC_ID,  "test_info.aa", [],  HTTPStatus.OK, "at level 2", True),
                             (ADD_FIELD, DOC_ID,  "test_info.aa.bb", [],  HTTPStatus.OK, "at level 3", True),
                             (ADD_FIELD, DOC_ID,  "test_info.aa.bb.cc", [],  HTTPStatus.OK, "at level 4", True),
                             (ADD_FIELD, DOC_ID,  "test_info.aa.bb.cc.dd", [],  HTTPStatus.OK, "at level 5", True),
                             (ADD_FIELD, DOC_ID,  "test_info.aa.bb.cc.dd.ee", [], HTTPStatus.OK, "at level 6", True),
                             (ADD_ATTRIBUTES, DOC_ID, "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "sugar"},
                                                                                                                    {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": True},
                                                                                                                    {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 29},
                                                                                                                    {"attr_name": "patient_weight", "attr_type": "float", "attr_value": 62.80},                                                                                                          
                                                                                                                    {"attr_name": "treatment_timeperiod",
                                                                                                                     "attr_type": "date", "attr_value": "20Mar1999"},
                                                                                                                    {"attr_name": "treatment", "attr_type": "string", "attr_value": "diabetics",
                                                                                                                     "note": "test in every 3 months", "confidence": "sugar_within_control", "last_edited_by": "IQVIA"},
                                                                                                                    {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "at level 6", True),
                             (ADD_ATTRIBUTES, DOC_ID, "level.a.b",
                              [{"attr_name": "", "attr_type": "", "attr_value": "", "note": "", "confidence": ""}],  HTTPStatus.OK, "Field level.a.b does not exist", False),
                             ("", DOC_ID, "test_info.aa.bb.cc.dd.ee", [],  HTTPStatus.NOT_FOUND, "Missing op", False),
                             (ADD_FIELD, DOC_ID, "test_info.aa.bb.cc.dd.ee.ff", [],  HTTPStatus.OK, "Not allow more than 6 level", False),
                             (ADD_FIELD, "", "default_field", [], HTTPStatus.OK, "default fields upto 6 level added", True),
                             (ADD_FIELD, "", "l1.l2.l3.l4.l5.l6", [], HTTPStatus.OK, "default fields upto 6 level added", True),
                             (ADD_FIELD, "", "l1.l2.l3.l4.l5.l6.l7", [], HTTPStatus.OK, "Not allow more than 6 level", False),
                             (ADD_ATTRIBUTES, "", "default_field", [{"attr_name": "Team", "attr_type": "string", "attr_value": "accordionTeam"}],  HTTPStatus.OK, "added default accordion attribute", True)
                         ])
def test_add_metadata(new_app_context, op, aidoc_id, field_name, attributes, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name,
        "attributes": attributes,
    })

    with client:
        logger.debug(
            f"test_add_metadata: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}, {attributes}]")
        response = client.put("/pd/api/v1/documents/add_meta_data",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)

        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == CONTENT_TYPE

        if valid:
            assert json.loads(response.data)['isAdded'] == True
            assert json.loads(response.data)['isDuplicate'] == False
            assert json.loads(response.data)['error'] == "False"
        if response.status_code == 200 and json.loads(response.data)['isAdded'] == False:
            assert json.loads(response.data)['error'] is not None
        if response.status_code == HTTPStatus.UNAUTHORIZED:
           assert json.loads(response.data)[
               'message'] == UNAUTHORIZED_MSG
       


"""
Test cases for duplicate data check
"""
@pytest.mark.order(4)
@pytest.mark.parametrize("op, aidoc_id, field_name, attributes, expected_status_cd, comments, valid",
                          [(ADD_ATTRIBUTES, DOC_ID, "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "sugar"},
                                                                                {"attr_name": "treatment_timeperiod", "attr_type": "date", "attr_value": "20Mar1999"},
                                                                                {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "Normal",True)
                          ])
def test_add_metadata_duplicate(new_app_context, op, aidoc_id, field_name, attributes, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name,
        "attributes": attributes,
    })
    
    with client:
        logger.debug(
            f"test_add_metadata_duplicate: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}, {attributes}]")
        response = client.put("/pd/api/v1/documents/add_meta_data",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)

        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == CONTENT_TYPE

        if valid:
            assert json.loads(response.data)['isDuplicate'] == True
            assert json.loads(response.data)['isAdded'] == False
            assert json.loads(response.data)['error'] == "duplication error"
        if response.status_code == 200 and json.loads(response.data)['isAdded'] == False:
            assert json.loads(response.data)['error'] is not None
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        
        
"""
Test cases for update metadata
"""
@pytest.mark.order(5)
@pytest.mark.parametrize("aidoc_id, field_name, attributes, expected_status_cd, comments, valid",
                         [(DOC_ID, "test_info.aa.bb.cc.dd.ee", [ {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": False},
                                                                {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 27},], HTTPStatus.OK, "Normal", True),
                            (DOC_ID, "test_info.aa.bb.cc.dd.ee", [ {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": True},
                                                                {"attr_name": "no_of_years", "attr_type": "float", "attr_value": 2.8},], HTTPStatus.OK, "Normal", True),
                             (DOC_ID, "test_info.aa.bb.cc.dd.ee", "", HTTPStatus.NOT_FOUND, "Missing attributes", False)
                         ])
def test_update_meta_data(new_app_context, aidoc_id, field_name, attributes, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict.update({
        "aidocId": aidoc_id,
        "fieldName": field_name,
        "attributes": attributes
    })

    with client:
        logger.debug(
            f"test_update_meta_data: Processing for unit test type [{comments}]: [{aidoc_id}, {field_name}, {attributes}]")
        response = client.post("/pd/api/v1/documents/add_update_meta_data",
                               json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == CONTENT_TYPE

        if valid:
            assert json.loads(response.data)['isAdded'] == True
            assert json.loads(response.data)['isDuplicate'] == False
            assert json.loads(response.data)['error'] == "False"
        if response.status_code == 200 and json.loads(response.data)['isAdded'] == False:
            assert json.loads(response.data)['error'] is not None
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        
        
"""
Test case for get metadata
"""
@pytest.mark.order(3)
@pytest.mark.parametrize("op, aidoc_id, field_name, expected_status_cd, comments, valid",
                         [(METADATA,DOC_ID, "test_info.aa.bb.cc.dd.ee", HTTPStatus.OK, "Normal", True),
                          (METAPARAM, DOC_ID, "test_info.aa.bb.cc.dd.ee", HTTPStatus.OK, "Normal", True),
                          ("metadataa", DOC_ID, "test_info.aa.bb.cc.dd.ee", HTTPStatus.NOT_FOUND, "incorrect input", False),
                          (METADATA, "", "", HTTPStatus.OK, "default accordion response", True),
                          (METADATA, "", "Summary", HTTPStatus.OK, "Summary response", True),
                          (METAPARAM, "", "", HTTPStatus.OK, "default accordion metaparam response", True)
                          ])
def test_get_metadata(new_app_context, op, aidoc_id, field_name, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name
    })
    with client:
        logger.debug(
            f"test_get_metadata_summary: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}]")
        response = client.get("/pd/api/v1/documents/meta_data_summary",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == CONTENT_TYPE

        if valid:
            assert json.loads(response.data) is not None
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        


"""
Test case for delete metadata
"""
@pytest.mark.order()
@pytest.mark.parametrize("op, aidoc_id, field_name, attribute_names, soft_delete, expected_status_cd, comments, valid",
                         [(DELETE_ATTRIBUTE, DOC_ID, "test_info.aa.bb.cc.dd.ee", ["no_of_years", "isHealthy","treatment_timeperiod", "treatment", "testFor", "treatment_week_timeperiod"], False, HTTPStatus.OK, "Normal", True),
                          (DELETE_FIELD, DOC_ID, "test_info", [], False, HTTPStatus.OK, "at level 1", True),
                          (DELETE_FIELD, DOC_ID, "test_info.aa", [], False, HTTPStatus.OK, "at level 2", True),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb", [], False, HTTPStatus.OK, "at level 3", True),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb.cc", [], False, HTTPStatus.OK, "at level 4", True),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb.cc.dd", [], False,  HTTPStatus.OK, "at level 5", True),
                          (DELETE_FIELD, DOC_ID, "test_info.aa.bb.cc.dd.ee", [], False, HTTPStatus.OK, "at level 6", True)
                          ])
def test_delete_metadata(new_app_context, op, aidoc_id, field_name, attribute_names, soft_delete, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name,
        "attribute_name": attribute_names,
        "softDelete":soft_delete
    })

    with client:
        logger.debug(
            f"test_delete_metadata: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}, {attribute_names}]")
        response = client.delete(DELETE_BASE_PATH,
                                 json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == CONTENT_TYPE

        if valid:
            assert json.loads(response.data)['isDeleted'] == True
            assert json.loads(response.data)['error'] == ""
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        


@pytest.mark.order(7)
@pytest.mark.parametrize("op, aidoc_id, field_name, attribute_names,soft_delete, expected_status_cd, comments, valid",
                         [(DELETE_FIELD, "", "default_field", [],False, HTTPStatus.OK, "default field in level-1 deleted", True),
                         (DELETE_FIELD, "", "l1.l2.l3.l4.l5.l6", [],False, HTTPStatus.OK, "default fields upto 6 level deleted", True),
                          ])
                         
def test_delete_metadata_end(new_app_context, op, aidoc_id, field_name, attribute_names, soft_delete, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name,
        "attribute_name": attribute_names,
        "softDelete":soft_delete
    })

    with client:
        logger.debug(
            f"test_delete_metadata: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}, {attribute_names}]")
        response = client.delete(DELETE_BASE_PATH,
                                 json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == CONTENT_TYPE

        if valid:
            assert json.loads(response.data)['isDeleted'] == True
            assert json.loads(response.data)['error'] == ""
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        