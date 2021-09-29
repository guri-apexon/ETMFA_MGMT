import logging
import os
from re import A
import pytest
import pytest_check as check
from etmfa.consts import Consts as consts
from etmfa.server.config import Config
from etmfa.db import document_compare, received_comparecomplete_event
from etmfa.db.db import db_context
from etmfa.db.models.documentcompare import Documentcompare
from sqlalchemy import or_



@pytest.mark.parametrize("aidocid, protocol_number, document_path, insert_flag",
                        [
                           ('bf729bbf-454e-437e-bcc1-d40962adb7a9', 'cicl.2c0f9dfa-e254-487c-b4c5-c47474552eea', r'./etmfa/tests/data/bf729bbf-454e-437e-bcc1-d40962adb7a9', 1),
                           ('bf729bbf-454e-437e-bcc1-d40962adb7a9', '', r'./etmfa/tests/data/bf729bbf-454e-437e-bcc1-d40962adb7a9', 0),
                           ('bf729bbf-454e-437e-bcc1-d40962adb7a9', 'cicl.2c0f9dfa-e254-487c-b4c5-c47474552eea', '', 0),
                        ])
def test_compare_functions(new_app_context, aidocid, protocol_number, document_path, insert_flag):
    try:
        _, _app_context = new_app_context
        with _app_context:
            compare_data = Documentcompare.query.filter(or_(Documentcompare.id1 == aidocid, Documentcompare.id2 == aidocid)).all()
            dict_ = dict()
            for row in compare_data:
                    dict_[(row.id1, row.id2, row.redactProfile)] = {
                        'compare_id': row.compareId,
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

            ids_compare_protocol = document_compare(aidocid, protocol_number, document_path)
            if ids_compare_protocol and insert_flag:
                for row in ids_compare_protocol:
                    dict_[(row['id1'], row['id2'], row['redact_profile'])]['compare_id'] = row['compareId']

                [received_comparecomplete_event(compare_dict, None) for id, compare_dict in dict_.items()]
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

