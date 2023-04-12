import json
import logging
from http import HTTPStatus
import pytest
from etmfa.consts import Consts as consts
from etmfa.server.config import Config

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("aidoc_id, expected_status_cd, comments",
                         [("aaf3a1bd-ea2e-4fab-8475-46bb43a7e25e", HTTPStatus.OK, "Normal"),
                          ("", HTTPStatus.NOT_FOUND, "Missing doc_id"),
                          ("a89de6a0-fc10-4964-9364-fa20962d44e",
                           HTTPStatus.NOT_FOUND, "Non existing doc_id")
                          ])
def test_get_dipa_view_by_doc_id(new_app_context, aidoc_id, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()

    input_dict = {"doc_id": aidoc_id}
    with client:
        logger.debug(
            f"test_get_dipa_view_by_doc_id: Processing for unit test type [{comments}]: [{aidoc_id}]")
        response = client.get("/pd/api/v1/documents/get_dipadata_by_doc_id",
                              json=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd


@pytest.mark.parametrize("category, doc_id, id, expected_status_cd, comments",
                         [("cpt_exclusion_criteria", "4afe7070-61d9-434d-aba4-5ca6f25b6117",
                           "ce357f04-4e8c-45d4-8ded-986fedef664e", HTTPStatus.OK, "Normal")
                          ])
def test_get_dipadata_by_category(new_app_context, category, doc_id, id, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"category": category, "doc_id": doc_id, "id": id}
    with client:
        logger.debug(
            f"test_get_protocols: Processing for unit test type [{comments}]: [{category}, {id}, {doc_id}]")
        response = client.get("/pd/api/v1/documents/get_dipadata_by_category",
                              data=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd


@pytest.mark.parametrize(
    "id, doc_id, link_id_1, link_id_2, link_id_3, link_id_4, link_id_5, link_id_6, category, dipa_data, "
    "userName,userId,expected_status_cd, comments",
    [("06d9b878-48b6-4106-820e-249511919fd0", "f79ee831-1a2d-4253-9b78-7c1abff51a1a", "", "", "", "", "", "", "",
      "", "Test User", "1155000", HTTPStatus.OK, "Normal")
     ])
def test_update_dipa_data(new_app_context, id, doc_id, category, link_id_1, link_id_2, link_id_3, link_id_4, link_id_5,
                          link_id_6, dipa_data, userName, userId, expected_status_cd, comments):
    new_app, _ = new_app_context
    client = new_app.test_client()
    input_dict = {"id": id, "doc_id": doc_id, "link_id_1": link_id_1, "link_id_2": link_id_2, "link_id_3": link_id_3,
                  "link_id_4": link_id_4, "link_id_5": link_id_5, "link_id_6": link_id_6, "category": category,
                  "dipa_data": dipa_data,"userName":userName,"userId":userId}
    with client:
        logger.debug(
            f"test_update_dipa_data: Processing for unit test type [{comments}]: [{id}, {doc_id}, {link_id_1}, {link_id_2}, {link_id_3}, {link_id_4}, {link_id_5},{link_id_6}, {category}, {dipa_data}]")
        response = client.put("/pd/api/v1/documents/update_dipa_data",
                              data=input_dict, headers=Config.UNIT_TEST_HEADERS)
        assert response.status_code == expected_status_cd
        if response.status_code == HTTPStatus.OK:
            assert json.loads(response.data)['response'] == "Successfully Inserted Data in DB"
