import pytest
from etmfa.server.config import Config


@pytest.mark.parametrize("doc_id, link_id, status_code, comments",
                         [("5c784c05-fbd3-4786-b0e4-3afa0d1c61ac", "", 200,
                           "doc id and without link id"), (
                          "1698be28-1cf3-466e-8f56-5fc920029056", "", 200,
                          "doc id changes"), (
                          "21552918-f506-43d8-8879-4fe532631ba7",
                          "8f8e70a7-cb76-4257-b595-80a2564a8aa2", 200,
                          "doc id and link id present"),
                          ("4c7ea27b-8a6b-4bf0-a8ed-2c1e49bbdc8c",
                           "46bac1b7-9197-11ed-b507-005056ab6469", 200,
                           "doc id and link id with enriched data")
                          ])
def test_document_data(new_app_context, doc_id, link_id, status_code,
                       comments):
    """
    Tests document enriched data for document with doc_id, link_id.
    """
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        get_enriched_data = client.get("/pd/api/cpt_data/get_enriched_terms",
                                       json={"aidoc_id": doc_id, "link_id": link_id},
                                       headers=Config.UNIT_TEST_HEADERS)
        assert get_enriched_data.status_code == status_code
