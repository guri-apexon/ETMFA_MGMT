import logging
import os
from re import A
import pytest
import pytest_check as check
from etmfa.consts import Consts as consts
from etmfa.server.config import Config
from etmfa.db import document_compare_all_permutations, received_comparecomplete_event
from etmfa.db.db import db_context
from etmfa.workflow.default_workflows import DWorkFLows
from etmfa.db.models.documentcompare import Documentcompare
from sqlalchemy import or_
import uuid



@pytest.mark.parametrize("aidocid,insert_flag",
                        [
                           # ('9f1f6bd8-3899-48b3-9629-69bdb5f83263', 'Redaction-SDS-PROT', r'./etmfa/tests/data/9f1f6bd8-3899-48b3-9629-69bdb5f83263', 1),
                           ('d11c55eb-2d2c-40ab-9be2-cd6019290eda', 0),
                        #    ('9f1f6bd8-3899-48b3-9629-69bdb5f83263', 0),
                        #    ('9f1f6bd8-3899-48b3-9629-69bdb5f83263', 0),
                        ])
def test_compare_functions(new_app_context, aidocid, insert_flag):
    try:
        _, _app_context = new_app_context
        with _app_context:
            compare_data = Documentcompare.query.filter(or_(Documentcompare.id1 == aidocid, Documentcompare.id2 == aidocid)).all()
            dict_ = dict()
            flow_id=uuid.uuid4()
            for row in compare_data:
                    dict_[(row.id1, row.id2, row.redactProfile)] = {
                        'compare_id': row.compareId,
                        'flow_id':flow_id,
                        'IQVXMLPath':row.compareIqvXmlPath,
                        'JSONPath': row.compareJSONPath,
                        'CSVPath': row.compareCSVPath,
                        'NumChangesTotal': str(row.numChangesTotal),
                        'CSVPathNormSOA': row.compareCSVPathNormSOA,
                        'JSONPathNormSOA': row.compareJSONPathNormSOA,
                        'redact_profile': row.redactProfile,
                        'id1':row.id1,
                        'id2':row.id2
                    }

            compare_data = Documentcompare.query.filter(or_(Documentcompare.id1 == aidocid, Documentcompare.id2 == aidocid)).delete()
            logging.info(f"Unit test : Cleared # of rows of [pd_protocol_compare: {compare_data}]")

            ids_compare_protocol = document_compare_all_permutations(db_context.session,aidocid,DWorkFLows.DOCUMENT_COMPARE.value)
            if ids_compare_protocol and insert_flag:
                for row in ids_compare_protocol:
                    dict_[(row['id1'], row['id2'], row['redact_profile'])]['compare_id'] = row['compare_id']

                [received_comparecomplete_event(db_context.session,compare_dict) for id, compare_dict in dict_.items()]
                compare_data = Documentcompare.query.filter(or_(Documentcompare.id1 == aidocid, Documentcompare.id2 == aidocid)).all()
                for row in compare_data:
                    assert row.compareCSVPath is not None and row.compareJSONPath is not None and row.compareIqvXmlPath is not None and row.createdDate <= row.updatedDate
            else:
                if insert_flag == 0:
                    assert True
                else:
                    assert False
                db_context.session.rollback()

    except Exception as ex:
        db_context.session.rollback()
        logging.error(ex)
        assert False

