import pytest
from etmfa.server.config import Config
from etmfa.server.namespaces.cptconfigapi import get_section_data


@pytest.mark.parametrize("doc_id, link_level, link_id, user_id, protocol, status_code, comments", [
    ("272c5cab-fbf3-44f8-8afe-3b8d419618bf", '3', "0a55c528-fee8-11ed-af21-005056ab6469", "Dig2_Batch_Tester",
     "cicl.06ed2096-0749-4ead-a892-9e57ead4fcbc", 200, "doc id and with link id and link_level 3"),
    ("1698be28-1cf3-466e-8f56-5fc920029056", "1", "", "1036048",
     "FEED_TEST4", 404, "doc id changes"),
    ("46d3456d-8aa2-4022-b251-b03271c151b3", "1", "c41f313b-9c40-456a-ac45-9c2e99aeabaa", "Dig2_Batch_Tester",
     "cicl.06ed2096-0749-4ead-a892-9e57ead4fcbc", 200, "doc id and link id present with level 1 all data"),
    ("4c7ea27b-8a6b-4bf0-a8ed-2c1e49bbdc8c", "1", "46bac1b7-9197-11ed-b507-005056ab6469", "Dig2_Batch_Tester",
     "005", 200, "doc id and link id with enriched data")
])
def test_document_object(new_app_context, user_id, protocol, doc_id, status_code, link_level, link_id, comments):
    """
        Tests document Section/Header data for document with doc_id, protocol, user_id, link_level and link_id.
    """
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        get_cpt_section_data = client.get("/pd/api/cpt_data/get_section_data",
                                          json={"aidoc_id": doc_id,
                                                "link_level": link_level,
                                                "link_id": link_id,
                                                "user_id": user_id,
                                                "protocol": protocol},
                                          headers=Config.UNIT_TEST_HEADERS)

        assert get_cpt_section_data.status_code == status_code


@pytest.mark.parametrize("aidoc_id, link_level, link_id, user_id, protocol", [
    ("272c5cab-fbf3-44f8-8afe-3b8d419618bf", 3, "0a55c528-fee8-11ed-af21-005056ab6469", "Dig2_Batch_Tester",
     "cicl.06ed2096-0749-4ead-a892-9e57ead4fcbc"),
    ("272c5cab-fbf3-44f8-8afe-3b8d419618bf", 2, "0a55c528-fee8-11ed-af21-005056ab6469", "mgmt",
         "005")
])
def test_get_section_data(new_app_context, aidoc_id, link_level, link_id, user_id, protocol):
    _, _app_context = new_app_context
    with _app_context:
        enrich_data = get_section_data(aidoc_id, link_level, link_id, user_id, protocol)

    if len(enrich_data) > 0:
        assert enrich_data[0].get('aidocid') == aidoc_id
