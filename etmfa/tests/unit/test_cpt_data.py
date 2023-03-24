import pytest
from etmfa.server.config import Config


@pytest.mark.parametrize("doc_id, link_level, toc, status_code, comments", [
    ("5c784c05-fbd3-4786-b0e4-3afa0d1c61ac", "1", "1", 200,
     "doc is present and toc is 1 data"),
    ("1698be28-1cf3-466e-8f56-5fc9200290571", "1",
     "1", 404, "doc id does not exists partial data"),
    ("1698be28-1cf3-466e-8f56-5fc920029057", "1", "2", 206, "toc changed")])
def test_document_header(new_app_context, doc_id, link_level, toc, status_code, comments):
    """
        Tests CPT Sections/Headers  list for a particular document with doc_id, link_level, toc, and comments.
    """
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        get_cpt = client.get("/pd/api/cpt_data/",
                             json={"aidoc_id": doc_id, "link_level": link_level,
                                   "toc": toc}, headers=Config.UNIT_TEST_HEADERS)
        assert get_cpt.status_code == status_code
