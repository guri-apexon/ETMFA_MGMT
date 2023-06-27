import pytest
from etmfa.server.config import Config
from etmfa.db.models.pd_users import User
from etmfa.db.models.pd_user_metrics import UserMetrics
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.db import db_context
from etmfa.utilities.user_metrics import create_or_update_user_metrics


@pytest.mark.parametrize("doc_id, link_level, toc, status_code, comments", [
    ("ec06c44f-3f09-46f7-9fa8-547916ca89d9", "1", "1", 200,
     "doc is present and toc is 1 data"),
    ("94770170-19c2-4a3e-9505-7e6b9c683b3d", "1", "1", 200,
     "doc is present and toc is 1 data"),
    ("580e2944-1d42-4df3-ae37-3cb59c483e4c", "2", "1", 200,
     "doc is present and toc is 1 data and link level is 2"),
    ("1698be28-1cf3-466e-8f56-5fc9200290571", "1",
     "1", 404, "doc id does not exists partial data"),
    ("1698be28-1cf3-466e-8f56-5fc920029057", "1", "2", 206, "toc changed")
])
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


@pytest.mark.parametrize("doc_id, user_id, results, comments", [
    ("0aaeec59-5e7b-42a5-8ac9-de3f9c35690d", "1156301", 1, "To create user metrics with count 1"),
    ("d0a9520d-2f7f-4b9f-b061-02988c6d68fc", "1156301", 2, "update user metrics user metrics with count "),
    ("0aaeec59-5e7b-42a5-8ac9-de3f9c35690d", "1156301", 2, "To update existing user metrics with count 2")
])
def test_user_metrics(new_app_context, doc_id, user_id, results, comments):
        _, app_context = new_app_context
        with app_context:
            db_context.session.query(UserMetrics).update({UserMetrics.userid: user_id, UserMetrics.isactive: True})
            create_or_update_user_metrics(user_id=user_id, aidoc_id=doc_id)
            user_filter = (user_id, 'u' + user_id, 'q' + user_id)
            user = db_context.session.query(User).filter(
                User.username.in_(user_filter)).first()
            protocol_obj = db_context.session.query(PDProtocolMetadata).filter(
                PDProtocolMetadata.id == doc_id).first()
            user_metrics = db_context.session.query(UserMetrics).filter(
                    UserMetrics.userid.in_(user_filter),
                    UserMetrics.aidoc_id == doc_id,
                    UserMetrics.user_type == user.user_type,
                    UserMetrics.document_version == protocol_obj.versionNumber).first()
            assert user_metrics.protocol == protocol_obj.protocol
            assert int(user_metrics.viewed_count) >= int(results)

            # To clean up the database entry
            if results == 2 and user_metrics:
                user_metrics = db_context.session.query(UserMetrics).filter(
                    UserMetrics.userid.in_(user_filter),
                    UserMetrics.aidoc_id == doc_id,
                    UserMetrics.user_type == user.user_type,
                    UserMetrics.document_version == protocol_obj.versionNumber).first()

                db_context.session.delete(user_metrics)
                db_context.session.commit()
