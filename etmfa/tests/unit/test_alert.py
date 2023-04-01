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
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata

@pytest.mark.parametrize("ai_doc_id, protocol_no, protocol_title, approval_date, insert_flag, comment",
                        [
                            ('8410e658-074a-4c6e-a45d-010d1663a0ca', 'test_compare_0213_K-877-302', 'PEMAFIBRATE TO REDUCE CARDIOVASCULAR OUTCOMES BY REDUCING TRIGLYCERIDES IN PATIENTS WITH DIABETES', '20200101', 1, "Entry in alert table to be made."),
                            ('b204ffb3-18c6-481a-9108-3c7745fdd6e6', 'test_compare_0213_K-877-302', 'PEMAFIBRATE TO REDUCE CARDIOVASCULAR OUTCOMES BY REDUCING TRIGLYCERIDES IN PATIENTS WITH DIABETES', '18990101', 0, "Entry in alert table not to be made."),
                            ('b204ffb3-18c6-481a-9108-3c7745fdd6e6', '', 'PEMAFIBRATE TO REDUCE CARDIOVASCULAR OUTCOMES BY REDUCING TRIGLYCERIDES IN PATIENTS WITH DIABETES', '20200101', 0, "Entry in alert table not to be made."),
                            ('b204ffb3-18c6-481a-9108-3c7745fdd6e6', 'test_compare_0213_K-877-302', 'PEMAFIBRATE TO REDUCE CARDIOVASCULAR OUTCOMES BY REDUCING TRIGLYCERIDES IN PATIENTS WITH DIABETES', '', 0, "Entry in alert table not to be made."),
                            ('b204ffb3-18c6-481a-9108-3c7745fdd6e6', 'test_compare_0213_K-877-302', 'PEMAFIBRATE TO REDUCE CARDIOVASCULAR OUTCOMES BY REDUCING TRIGLYCERIDES IN PATIENTS WITH DIABETES', '202001', 0, "Entry in alert table not to be made.")
                        ])
def test_alert_functions(new_app_context, ai_doc_id, protocol_no, protocol_title, approval_date, insert_flag, comment):
    try:
        _, _app_context = new_app_context
        with _app_context:
            finalattributes = dict()

            finalattributes['AiDocId'] = ai_doc_id
            finalattributes['ProtocolNo'] = protocol_no
            finalattributes['ProtocolTitle'] = protocol_title
            finalattributes['approval_date'] = approval_date

            alert_res = Protocolalert.query.filter(and_(Protocolalert.protocol == finalattributes['ProtocolNo'],
                                                        Protocolalert.aidocId == finalattributes['AiDocId'])).delete()

            protocolMetadata = db_context.session.query(PDProtocolMetadata).filter(PDProtocolMetadata.protocol == protocol_no).all()
            meta_data_dict = dict()
            for row in protocolMetadata:
                meta_data_dict[row.id] = row.status
            del(protocolMetadata)

            logging.info(f"Unit test : Cleared # of rows of [pd_protocol_alert: {alert_res}]")

            db_context.session.commit()

            insert_into_alert_table(finalattributes,{})

            protocolMetadata = db_context.session.query(PDProtocolMetadata).filter(
                and_(PDProtocolMetadata.protocol == protocol_no, PDProtocolMetadata.status == 'ERROR')).all()

            for row in protocolMetadata:
                row.status = 'PROCESS_COMPLETED'
                row.errorCode = None
                row.errorReason = None
                db_context.session.add(row)
            db_context.session.commit()

            alert_res = Protocolalert.query.filter(and_(Protocolalert.protocol == finalattributes['ProtocolNo'],
                                                        Protocolalert.aidocId == finalattributes['AiDocId'])).all()

            if insert_flag == 1:
                assert len(alert_res) >= 1
            else:
                assert len(alert_res) == 0

            protocolMetadata = db_context.session.query(PDProtocolMetadata).filter(and_(PDProtocolMetadata.protocol == protocol_no,PDProtocolMetadata.status == 'ERROR')).all()

            for row in protocolMetadata:
                row.status = 'PROCESS_COMPLETED'
                row.errorCode = None
                row.errorReason = None
                db_context.session.add(row)
            db_context.session.commit()

    except Exception as ex:
        db_context.session.rollback()
        logging.error(ex)
        assert False


