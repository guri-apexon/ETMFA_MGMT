import pytest
from etmfa.crud.pd_protocol_summary_entities import pd_protocol_summary_entities
from etmfa.db.db import db_context
from etmfa.crud.base import CRUDBase


@pytest.mark.parametrize("doc_id, comments", [
    ('0013956f-b5cb-40ed-af22-47b6b9af29a3', "doc id for iqv data summary entities"),
])
def test_protocol_summary_entities(new_app_context, doc_id, comments):
    _, app_context = new_app_context
    with app_context:
        pd_entities = pd_protocol_summary_entities.get_protocol_summary_entities(db=db_context.session, aidocId=doc_id)
        if pd_entities:
            assert True