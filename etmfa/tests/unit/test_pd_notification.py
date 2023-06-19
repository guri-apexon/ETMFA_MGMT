import pytest
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.server.config import Config


@pytest.mark.parametrize("doc_id, event, send_mail, test_case, status_code, comments", [
    ("5c784c05-fbd3-4786-b0e4-3afa0d1c61ac", "QC_COMPLETED",False, False,200,
     "doc id with QC-COMPLETED event"),
    ("5c784c05-fbd3-4786-b0e4-3afa0d1c61ac",  "EVENT_NOT_EXISTS", False, False, 400,
     "doc id with event does not exists"),
    ("5c784c05-fbd3-4786-b0e4-3afa0d1c61ac", "QC_COMPLETED", True, True, 200,
     "doc id with QC-COMPLETED event"),
    ("4c7ea27b-8a6b-4bf0-a8ed-2c1e49bbdc8c", "QC_COMPLETED", True, True, 200,
     "doc id with QC-COMPLETED event and send mail and test case"),
    ("4c7ea27b-8a6b-4bf0-a8ed-2c1e49bbdc8c", "EDITED", True, True, 200,
     "doc id with QC-COMPLETED event and send mail and test case"),
])
def test_email_notifications(new_app_context, doc_id, event, status_code, send_mail, test_case, comments):
    """
        Tests PD email notification endpoint for a particular document with event and comments.
    """
    new_app, _ = new_app_context
    client = new_app.test_client()

    with client:
        get_cpt = client.get("/pd/api/v1/documents/notifications/send/email",
                             json={"doc_id": doc_id, "event": event, "send_mail":send_mail, "test_case":test_case}, headers=Config.UNIT_TEST_HEADERS)
        assert get_cpt.status_code == status_code


def test_edited_event_notification(new_app_context):
    """
    Test case for edited event notification and event alert emails trigger
    """
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        response = client.get("/pd/api/v1/documents/notifications/send/edited/emails",
                              json={"test_case": True},
                              headers=Config.UNIT_TEST_HEADERS
                              )
        assert response.status_code == 200