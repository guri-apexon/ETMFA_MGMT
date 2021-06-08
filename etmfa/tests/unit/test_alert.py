import logging

import pandas as pd
import pytest
import pytest_check as check
from etmfa.consts import Consts as consts
from etmfa.server.config import Config
from etmfa.db import insert_into_alert_table
from etmfa.db.db import db_context
from sqlalchemy import and_
from etmfa.db.models.pd_protocol_alert import Protocolalert



@pytest.mark.parametrize("ai_doc_id, user_id, protocol_no, short_title, approval_date, insert_flag, comment",
                        [('8410e658-074a-4c6e-a45d-010d1663a0ca', 'alert_test_user', 'test_compare_0213_K-877-302', '', '20200101', 1, "Entry in alert table to be made."),
                         ('b204ffb3-18c6-481a-9108-3c7745fdd6e6', 'alert_test_user_1', 'test_compare_0213_K-877-302', '', '18990101', 0, "Entry in alert table not to be made."),
                         ('b204ffb3-18c6-481a-9108-3c7745fdd6e6', '', 'test_compare_0213_K-877-302', '', '20200101', 0, "Entry in alert table not to be made."),
                         ('b204ffb3-18c6-481a-9108-3c7745fdd6e6', 'alert_test_user_1', '', '', '20200101', 0, "Entry in alert table not to be made."),
                         ('b204ffb3-18c6-481a-9108-3c7745fdd6e6', 'alert_test_user_1', 'test_compare_0213_K-877-302', '', '', 0, "Entry in alert table not to be made."),
                         ('8410e658-074a-4c6e-a45d-010d1663a0ca', 'alert_test_user', 'test_compare_0213_K-877-302', '', '202001', 0, "Entry in alert table to be made.")
                        ])
def test_alert_functions(new_app_context, ai_doc_id, user_id, protocol_no, short_title, approval_date, insert_flag, comment):
    try:
        _, _app_context = new_app_context
        with _app_context:
            finalattributes = dict()

            finalattributes['AiDocId'] = ai_doc_id
            finalattributes['UserId'] = user_id
            finalattributes['ProtocolNo'] = protocol_no
            finalattributes['ShortTitle'] = short_title
            finalattributes['approval_date'] = approval_date

            alert_res = Protocolalert.query.filter(and_(Protocolalert.protocol == finalattributes['ProtocolNo'],
                                                        Protocolalert.aidocId == finalattributes['AiDocId'])).delete()

            logging.info(f"Unit test : Cleared # of rows of [pd_protocol_alert: {alert_res}]")

            db_context.session.commit()

            insert_into_alert_table(finalattributes)

            alert_res = Protocolalert.query.filter(and_(Protocolalert.protocol == finalattributes['ProtocolNo'],
                                                        Protocolalert.aidocId == finalattributes['AiDocId'])).all()

            if insert_flag == 1:
                assert len(alert_res) >= 1
            else:
                assert len(alert_res) == 0

    except Exception as ex:
        db_context.session.rollback()
        logging.error(ex)


