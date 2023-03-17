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
input_dict = {
    "op": '',
    "aidocId": '',
    "fieldName": ''
}
"""
Test cases for delete data if exists
"""
@pytest.mark.order(1)
@pytest.mark.parametrize("op, aidoc_id, field_name, attribute_names, expected_status_cd, comments",
                         [ ("deleteField", "", "summary_extended", [],
                                 HTTPStatus.OK, "delete summary_extended if there only for consistency"),
                          ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee", [],
                                 HTTPStatus.OK, "delete field if there only for consistency"),
                          ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc.dd.ee", [],  HTTPStatus.OK, "at level 6"),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc.dd", [],  HTTPStatus.OK, "at level 5"),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc", [],  HTTPStatus.OK, "at level 4"),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb", [],  HTTPStatus.OK, "at level 3"),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa", [],  HTTPStatus.OK, "at level 2"),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info", [], HTTPStatus.OK, "at level 1"),
                        ])
                         
def test_delete_metadata_start(new_app_context, op, aidoc_id, field_name, attribute_names, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name
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
@pytest.mark.order(3)
@pytest.mark.parametrize("op, aidoc_id, field_name, attributes, expected_status_cd, comments,valid",
                         [
                             ("addField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info", [],  HTTPStatus.OK, "at level 1", True),
                             ("addField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa", [],  HTTPStatus.OK, "at level 2", True),
                             ("addField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb", [],  HTTPStatus.OK, "at level 3", True),
                             ("addField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc", [],  HTTPStatus.OK, "at level 4", True),
                             ("addField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc.dd", [],  HTTPStatus.OK, "at level 5", True),
                             ("addField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc.dd.ee", [], HTTPStatus.OK, "at level 6", True),
                             ("addAttributes", "00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "sugar"},
                                                                                                                    {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": True},
                                                                                                                    {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 29},
                                                                                                                    {"attr_name": "treatment_timeperiod",
                                                                                                                     "attr_type": "date", "attr_value": "20Mar1999"},
                                                                                                                    {"attr_name": "treatment", "attr_type": "string", "attr_value": "diabetics",
                                                                                                                     "note": "test in every 3 months", "confidence": "sugar_within_control"},
                                                                                                                    {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "at level 6", True),
                             ("addAttributes", "00263eb0-7713-4abc-ab38-bcebac2b0437", "level.a.b",
                              [{"attr_name": "", "attr_type": "", "attr_value": "", "note": "", "confidence": ""}],  HTTPStatus.OK, "Field level.a.b does not exist", False),
                             
                             ("", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                                 "test_info.aa.bb.cc.dd.ee", [],  HTTPStatus.NOT_FOUND, "Missing op", False),
                             ("addField", "00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee.ff",
                                 [],  HTTPStatus.NOT_FOUND, "Not allow more than 6 level", False),
                             ("addField", "", "summary_extended.l1.l2.l3.l4.l5", [],
                                 HTTPStatus.OK, "summary_extended fields added", True),
                             ("addField", "", "summary_extended.l1.l2.l3.l4.l5.l6", [],
                                 HTTPStatus.NOT_FOUND, "Not allow more than 6 level", False),
                             ("addAttributes", "", "summary_extended",
                              [{"attr_name": "Team", "attr_type": "string", "attr_value": "accordionTeam", "note": "", "confidence": ""}],  HTTPStatus.OK, "added in summary_extended", True)
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
            assert json.loads(response.data)['is_added'] == True
            assert json.loads(response.data)['is_duplicate'] == False
            assert json.loads(response.data)['error'] == "False"
        if response.status_code == 200 and json.loads(response.data)['is_added'] == False:
            assert json.loads(response.data)['error'] is not None
        if response.status_code == HTTPStatus.UNAUTHORIZED:
           assert json.loads(response.data)[
               'message'] == UNAUTHORIZED_MSG
       


"""
Test cases for duplicate data check
"""
@pytest.mark.order(4)
@pytest.mark.parametrize("op, aidoc_id, field_name, attributes, expected_status_cd, comments, valid",
                         [("addField", "00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee", [],  HTTPStatus.OK, "Normal",True),
                          ("addAttributes", "00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "sugar"},
                                                                                                                 {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": False},
                                                                                                                 {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 27},
                                                                                                                 {"attr_name": "treatment_timeperiod", "attr_type": "date", "attr_value": "20Mar1999"},
                                                                                                                 {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "Normal",True),
                          ("addField", "", "summary_extended", [], HTTPStatus.OK, "Normal", True)
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
            assert json.loads(response.data)['is_duplicate'] == True
            assert json.loads(response.data)['is_added'] == False
            assert json.loads(response.data)['error'] == "duplication error"
        if response.status_code == 200 and json.loads(response.data)['is_added'] == False:
            assert json.loads(response.data)['error'] is not None
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        
        
"""
Test cases for update metadata
"""
@pytest.mark.order(5)
@pytest.mark.parametrize("aidoc_id, field_name, attributes, expected_status_cd, comments, valid",
                         [
                             
                             ("00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "blood"},
                                                                                                   {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": True},
                                                                                                   {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 28},
                                                                                                   {"attr_name": "treatment_timeperiod",
                                                                                                    "attr_type": "date", "attr_value": "21Mar1999"},
                                                                                                   {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "Normal", True),
   
                             ("00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee", [
                                 {"attr_name": "testFor", "attr_type": "string", "attr_value": "blood"}], HTTPStatus.OK, "Normal", True),
                             
                             
                             ("00263eb0-7713-4abc-ab38-bcebac2b0437",
                                 "test_info.aa.bb.cc.dd.ee", "", HTTPStatus.NOT_FOUND, "Missing attributes", False),
                             ("", "summary_extended", [{"attr_name": "Team", "attr_type": "string", "attr_value": "accordionMetaTeam"}], HTTPStatus.OK, "summary_extended fields added", True),
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
            assert json.loads(response.data)['is_added'] == True
            assert json.loads(response.data)['is_duplicate'] == False
            assert json.loads(response.data)['error'] == "False"
        if response.status_code == 200 and json.loads(response.data)['is_added'] == False:
            assert json.loads(response.data)['error'] is not None
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        
        
"""
Test case for get metadata
"""
@pytest.mark.order(2)
@pytest.mark.parametrize("op, aidoc_id, field_name, expected_status_cd, comments, valid",
                         [("metadata", "00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee", HTTPStatus.OK, "Normal", True),
                          ("metaparam", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                           "test_info.aa.bb.cc.dd.ee", HTTPStatus.OK, "Normal", True),
                          ("metadataa", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                           "test_info.aa.bb.cc.dd.ee", HTTPStatus.NOT_FOUND, "incorrect input", False),
                          ("metadata", "", "", HTTPStatus.OK, "summary_extended response", True),
                          ("metadata", "", "summary_extended", HTTPStatus.OK, "summary_extended response", True),
                          ("metaparam", "", "", HTTPStatus.OK, "summary_extended metaparam response", True)
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
@pytest.mark.order(6)
@pytest.mark.parametrize("op, aidoc_id, field_name, attribute_names, expected_status_cd, comments, valid",
                         [
                          ("", "00263eb0-7713-4abc-ab38-bcebac2b0437", "test_info.aa.bb.cc.dd.ee",
                           ["num_houses"],  HTTPStatus.NOT_FOUND, "Missing op", False),
                         
                          ("deleteAttribute", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                           "test_info.aa.bb.cc.dd.ee", ["no_of_years", "isHealthy","treatment_timeperiod", "treatment", "testFor", "treatment_week_timeperiod"],  HTTPStatus.OK, "Normal", True),
                          
                          ("deleteField", "", "test_info.aa.bb.cc.dd.ee",
                           [],  HTTPStatus.OK, "Normal", True),
                          ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info", [],  HTTPStatus.OK, "at level 1", True),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa", [],  HTTPStatus.OK, "at level 2", True),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb", [],  HTTPStatus.OK, "at level 3", True),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc", [],  HTTPStatus.OK, "at level 4", True),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc.dd", [],  HTTPStatus.OK, "at level 5", True),
                             ("deleteField", "00263eb0-7713-4abc-ab38-bcebac2b0437",
                              "test_info.aa.bb.cc.dd.ee", [], HTTPStatus.OK, "at level 6", True),
                          ("deleteAttribute","", "summary_extended", ["Sponsor", "testFor", "Team"], HTTPStatus.OK, "summary_extended fields deleted", True)
                          ])
def test_delete_metadata(new_app_context, op, aidoc_id, field_name, attribute_names, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name,
        "attributeName": attribute_names
    })

    with client:
        logger.debug(
            f"test_delete_metadata: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}, {attribute_names}]")
        response = client.delete(DELETE_BASE_PATH,
                                 json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == CONTENT_TYPE

        if valid:
            assert json.loads(response.data)['is_deleted'] == True
            assert json.loads(response.data)['error'] == ""
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        


@pytest.mark.order(7)
@pytest.mark.parametrize("op, aidoc_id, field_name, attribute_names, expected_status_cd, comments, valid",
                         [
                          ("deleteField","", "summary_extended", [], HTTPStatus.OK, "summary_extended fields deleted", True)
                           ]
                         )
def test_delete_metadata_end(new_app_context, op, aidoc_id, field_name, attribute_names, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict.update({
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name,
        "attributeName": attribute_names
    })

    with client:
        logger.debug(
            f"test_delete_metadata: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}, {attribute_names}]")
        response = client.delete(DELETE_BASE_PATH,
                                 json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == CONTENT_TYPE

        if valid:
            assert json.loads(response.data)['is_deleted'] == True
            assert json.loads(response.data)['error'] == ""
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == UNAUTHORIZED_MSG
        