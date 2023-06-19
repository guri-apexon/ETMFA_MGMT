import pytest
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_documenttables_db import DocumenttablesDb
from etmfa.db.db import db_context
from etmfa.crud.base import CRUDBase


@pytest.mark.parametrize("doc_id, comments", [
    ('272c5cab-fbf3-44f8-8afe-3b8d419618bf', "doc id for base function"),
])
def test_base(new_app_context, doc_id, comments):
    _, app_context = new_app_context
    with app_context:
        first_record_from_crud = CRUDBase(DocumenttablesDb).get(db=db_context.session, id=doc_id)
        assert first_record_from_crud == db_context.session.query(DocumenttablesDb).filter(DocumenttablesDb.id == doc_id).first()
        count_of_all_record = len(CRUDBase(PDProtocolMetadata).get_all(db=db_context.session))
        assert count_of_all_record <= db_context.session.query(PDProtocolMetadata).count()