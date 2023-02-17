import json
import logging
from http import HTTPStatus

import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

"""
Test cases for add data
"""
# add metadata


@pytest.mark.order(1)
@pytest.mark.parametrize("op, aidocId, fieldName, attributeNames, expected_status_cd, comments",
                         [("deleteField", "0be44992-9573-4010-962c-de1a1b18b08d", "test_info",
                           [],  HTTPStatus.OK, "delete record if there only for consistency")]
                         )
def test_delete_metadata_start(new_app_context, op, aidocId, fieldName, attributeNames, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict = {
        "op": op,
        "aidocId": aidocId,
        "fieldName": fieldName
    }

    with client:
        logger.debug(
            f"test_delete_metadata: Processing for unit test type [{comments}]: [{op}, {aidocId}, {fieldName}, {attributeNames}]")
        response = client.delete("/pd/api/v1/documents/delete_meta_data",
                                 json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd


@pytest.mark.order(3)
@pytest.mark.parametrize("op, aidocId, fieldName, attributes, expected_status_cd, comments,valid",
                         [
                             ("addField", "0be44992-9573-4010-962c-de1a1b18b08d",
                              "test_info", [],  HTTPStatus.OK, "at level 1", True),
                             ("addField", "0be44992-9573-4010-962c-de1a1b18b08d",
                              "test_info.aa", [],  HTTPStatus.OK, "at level 2", True),
                             ("addField", "0be44992-9573-4010-962c-de1a1b18b08d",
                              "test_info.aa.bb", [],  HTTPStatus.OK, "at level 3", True),
                             ("addField", "0be44992-9573-4010-962c-de1a1b18b08d",
                              "test_info.aa.bb.cc", [],  HTTPStatus.OK, "at level 4", True),
                             ("addField", "0be44992-9573-4010-962c-de1a1b18b08d",
                              "test_info.aa.bb.cc.dd", [],  HTTPStatus.OK, "at level 5", True),
                             ("addField", "0be44992-9573-4010-962c-de1a1b18b08d",
                              "test_info.aa.bb.cc.dd.ee", [], HTTPStatus.OK, "at level 6", True),
                             ("addAttributes", "0be44992-9573-4010-962c-de1a1b18b08d", "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "sugar"},
                                                                                                                    {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": True},
                                                                                                                    {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 29},
                                                                                                                    {"attr_name": "treatment_timeperiod",
                                                                                                                     "attr_type": "date", "attr_value": "20Mar1999"},
                                                                                                                    {"attr_name": "treatment", "attr_type": "string", "attr_value": "diabetics",
                                                                                                                     "note": "test in every 3 months", "confidence": "sugar_within_control"},
                                                                                                                    {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "at level 6", True),
                             ("addAttributes", "0be44992-9573-4010-962c-de1a1b18b08d", "level.a.b",
                              ["", "", "",],  HTTPStatus.OK, "missing attributes value", False),
                             ("", "", "", "",  HTTPStatus.NOT_FOUND,
                              "All missing", False),
                             ("", "0be44992-9573-4010-962c-de1a1b18b08d",
                                 "level.a.b", [],  HTTPStatus.NOT_FOUND, "Missing op", False),
                             ("addField", "", "level.aa.bb", [],
                                 HTTPStatus.NOT_FOUND, "Missing aidocId", False),
                             ("addField", "0be44992-9573-4010-962c-de1a1b18b08d", "alphabet.aa.bb.cc.dd.ee.ff",
                                 [],  HTTPStatus.NOT_FOUND, "Not allow more than 6 level", False),
                         ])
def test_add_metadata(new_app_context, op, aidocId, fieldName, attributes, expected_status_cd, comments, valid):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {
        "op": op,
        "aidocId": aidocId,
        "fieldName": fieldName,
        "attributes": attributes,
    }

    with client:
        logger.debug(
            f"test_add_metadata: Processing for unit test type [{comments}]: [{op}, {aidocId}, {fieldName}, {attributes}]")
        response = client.put("/pd/api/v1/documents/add_meta_data",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)

        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == "application/json"

        if valid:
            assert json.loads(response.data)['isAdded'] == True
            assert json.loads(response.data)['isDuplicate'] == False
            assert json.loads(response.data)['error'] == "False"
        if response.status_code == HTTPStatus.UNAUTHORIZED:
           assert json.loads(response.data)[
               'message'] == "Credential validation: Authentication failed for given username and password"


@pytest.mark.order(4)
@pytest.mark.parametrize("op, aidocId, fieldName, attributes, expected_status_cd, comments",
                         [("addField", "0be44992-9573-4010-962c-de1a1b18b08d", "test_info.aa.bb.cc.dd.ee", [],  HTTPStatus.OK, "duplication error"),
                          ("addAttributes", "0be44992-9573-4010-962c-de1a1b18b08d", "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "sugar"},
                                                                                                                 {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": False},
                                                                                                                 {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 27},
                                                                                                                 {"attr_name": "treatment_timeperiod",
                                                                                                                  "attr_type": "date", "attr_value": "20Mar1999"},
                                                                                                                 {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "duplication error")
                          ])
def test_add_metadata_duplicate(new_app_context, op, aidocId, fieldName, attributes, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {
        "op": op,
        "aidocId": aidocId,
        "fieldName": fieldName,
        "attributes": attributes,
    }
    print('in order 3')
    with client:
        logger.debug(
            f"test_add_metadata_duplicate: Processing for unit test type [{comments}]: [{op}, {aidocId}, {fieldName}, {attributes}]")
        response = client.put("/pd/api/v1/documents/add_meta_data",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)

        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == "application/json"

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['isDuplicate'] == True
            assert json.loads(response.data)['isAdded'] == False
            assert json.loads(response.data)['error'] == "duplication error"
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == "Credential validation: Authentication failed for given username and password"


"""
Test cases for update metadata
"""
# update metadata


@pytest.mark.order(5)
@pytest.mark.parametrize("aidocId, fieldName, attributes, expected_status_cd, comments",
                         [("0be44992-9573-4010-962c-de1a1b18b08d", "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "blood"},
                                                                                                {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": True},
                                                                                                {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 28},
                                                                                                {"attr_name": "treatment_timeperiod",
                                                                                                 "attr_type": "date", "attr_value": "21Mar1999"},
                                                                                                {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "Normal"),
                          ("0be44992-9573-4010-962c-de1a1b18b08d", "", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "blood"},
                                                                        {"attr_name": "isHealthy", "attr_type": "boolean", "attr_value": True},
                                                                        {"attr_name": "no_of_years", "attr_type": "integer", "attr_value": 28},
                                                                        {"attr_name": "treatment_timeperiod",
                                                                            "attr_type": "date", "attr_value": "21Mar1999"},
                                                                        {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "without field name"),
                          ("0be44992-9573-4010-962c-de1a1b18b08d", "test_info.aa.bb.cc.dd.ee", [
                           {"attr_name": "testFor", "attr_type": "string", "attr_value": "blood"}], HTTPStatus.OK, "Normal"),
                          ("", "test_info.aa.bb.cc.dd.ee", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "blood"},
                                                            {"attr_name": "isHealthy",
                                                             "attr_type": "boolean", "attr_value": True},
                                                            {"attr_name": "no_of_years",
                                                             "attr_type": "integer", "attr_value": 28},
                                                            {"attr_name": "treatment_timeperiod",
                                                             "attr_type": "date", "attr_value": "21Mar1999"},
                                                            {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.NOT_FOUND, "Missing aidocId"),
                          ("", "", "", HTTPStatus.NOT_FOUND, "All missing"),
                          ("0be44992-9573-4010-962c-de1a1b18b08d",
                           "test_info.aa.bb.cc.dd.ee", "", HTTPStatus.NOT_FOUND, "Normal")
                          ])
def test_update_meta_data(new_app_context, aidocId, fieldName, attributes, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {
        "aidocId": aidocId,
        "fieldName": fieldName,
        "attributes": attributes
    }

    with client:
        logger.debug(
            f"test_update_meta_data: Processing for unit test type [{comments}]: [{aidocId}, {fieldName}, {attributes}]")
        response = client.post("/pd/api/v1/documents/add_update_meta_data",
                               json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == "application/json"

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['isAdded'] == True
            assert json.loads(response.data)['isDuplicate'] == False
            assert json.loads(response.data)['error'] == "False"
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == "Credential validation: Authentication failed for given username and password"


"""
Get meta data
"""
# get metadata


@pytest.mark.order(6)
@pytest.mark.parametrize("op, aidoc_id, field_name, expected_status_cd, comments",
                         [("metadata", "0be44992-9573-4010-962c-de1a1b18b08d", "test_info.aa.bb.cc.dd.ee", HTTPStatus.OK, "Normal"),
                          ("metaparam", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "test_info.aa.bb.cc.dd.ee", HTTPStatus.OK, "Normal"),
                          ("metadata", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "test_info.aa.bb.cc.dd.ee", HTTPStatus.OK, "Normal"),
                          ("metadata", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "",  HTTPStatus.OK, "Normal"),
                          ("metaparam", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "", HTTPStatus.OK, "Normal"),
                          ("metadataa", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "test_info.aa.bb.cc.dd.ee", HTTPStatus.NOT_FOUND, "incorrect input"),
                          ("", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "", HTTPStatus.NOT_FOUND, "Missing op value"),
                          ("metadata", "", "", HTTPStatus.NOT_FOUND, "Missing aidocId"),
                          ("", "", "", HTTPStatus.NOT_FOUND, "All missing")
                          ])
def test_get_metadata(new_app_context, op, aidoc_id, field_name, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {
        "op": op,
        "aidocId": aidoc_id,
        "fieldName": field_name
    }
    with client:
        logger.debug(
            f"test_get_metadata_summary: Processing for unit test type [{comments}]: [{op}, {aidoc_id}, {field_name}]")
        response = client.get("/pd/api/v1/documents/meta_data_summary",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == "application/json"

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data) is not None
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == "Credential validation: Authentication failed for given username and password"


"""
Delete metadata
"""
# delete field and attribute


@pytest.mark.order(7)
@pytest.mark.parametrize("op, aidocId, fieldName, attributeNames, expected_status_cd, comments",
                         [("deleteField", "0be44992-9573-4010-962c-de1a1b18b08d", "test_info.aa.bb.cc.dd.ee", [],  HTTPStatus.OK, "delete at level 6"),
                          ("deleteField", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "level.a.b.", [],  HTTPStatus.OK, "delete at level 3 "),
                          ("deleteAttribute", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "test_info.aa.bb.cc.dd.ee", ["testFor"],  HTTPStatus.OK, "Normal"),
                          ("deleteAttribute", "0be44992-9573-4010-962c-de1a1b18b08d", "level.a.b", [{"attr_name": "testFor", "attr_type": "string", "attr_value": "sugar"},
                                                                                                    {"attr_name": "treatment_week_timeperiod", "attr_type": "array", "attr_value": ["mon", "thu"]}], HTTPStatus.OK, "at level 3"),
                          ("deleteField", "", "test_info.aa.bb.cc.dd.ee",
                           "",  HTTPStatus.NOT_FOUND, "Missing aidocId"),
                          ("deleteField", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "", "",  HTTPStatus.NOT_FOUND, "Field name missing"),
                          ("", "0be44992-9573-4010-962c-de1a1b18b08d", "test_info.aa.bb.cc.dd.ee",
                           ["num_houses"],  HTTPStatus.NOT_FOUND, "Missing op"),
                          ("", "", "", "",  HTTPStatus.NOT_FOUND, "All missing"),
                          ("deleteAttribute", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "test_info.aa.bb.cc.dd.ee", ["no_of_years", "isHealthy"],  HTTPStatus.OK, "Normal"),
                          ("deleteAttribute", "0be44992-9573-4010-962c-de1a1b18b08d", "",
                           ["no_of_years", "isHealthy"],  HTTPStatus.NOT_FOUND, "Field name missing")
                          ])
def test_delete_metadata(new_app_context, op, aidocId, fieldName, attributeNames, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict = {
        "op": op,
        "aidocId": aidocId,
        "fieldName": fieldName,
        "attributeName": attributeNames
    }

    with client:
        logger.debug(
            f"test_delete_metadata: Processing for unit test type [{comments}]: [{op}, {aidocId}, {fieldName}, {attributeNames}]")
        response = client.delete("/pd/api/v1/documents/delete_meta_data",
                                 json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == "application/json"

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['isDeleted'] == True
            assert json.loads(response.data)['error'] == ""
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == "Credential validation: Authentication failed for given username and password"


@pytest.mark.order(8)
@pytest.mark.parametrize("op, aidocId, fieldName, attributeNames, expected_status_cd, comments",
                         [("deleteField", "0be44992-9573-4010-962c-de1a1b18b08d",
                           "test_info", [],  HTTPStatus.OK, "delete record if there")]
                         )
def test_delete_metadata_end(new_app_context, op, aidocId, fieldName, attributeNames, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict = {
        "op": op,
        "aidocId": aidocId,
        "fieldName": fieldName,
        "attributeName": attributeNames
    }

    with client:
        logger.debug(
            f"test_delete_metadata: Processing for unit test type [{comments}]: [{op}, {aidocId}, {fieldName}, {attributeNames}]")
        response = client.delete("/pd/api/v1/documents/delete_meta_data",
                                 json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        assert response.headers["Content-Type"] == "application/json"

        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['isDeleted'] == True
            assert json.loads(response.data)['error'] == ""
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            assert json.loads(response.data)[
                'message'] == "Credential validation: Authentication failed for given username and password"
