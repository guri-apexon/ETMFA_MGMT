import pytest
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.server.config import Config


@pytest.mark.parametrize("doc_id, event, status_code, comments", [
    ("5c784c05-fbd3-4786-b0e4-3afa0d1c61ac", "QC_COMPLETED", 200,
     "doc id with QC-COMPLETED event"),
    ("5c784c05-fbd3-4786-b0e4-3afa0d1c61ac", "EVENT_NOT_EXISTS", 400,
     "doc id with event does not exists"),
])
def test_email_notifications(new_app_context, doc_id, event, status_code, comments):
    """
        Tests PD email notification endpoint for a particular document with event and comments.
    """
    new_app, _ = new_app_context
    client = new_app.test_client()

    with client:
        get_cpt = client.get("/pd/api/v1/documents/notifications/send/email",
                             json={"doc_id": doc_id, "event": event, }, headers=Config.UNIT_TEST_HEADERS)
        assert get_cpt.status_code == status_code
