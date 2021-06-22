import logging
from etmfa.db import utils, generate_email

import pytest
import pytest_check as check
from etmfa.consts import Consts as consts
from etmfa.server.config import Config
from sqlalchemy import and_
from etmfa.db.db import db_context
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.db.models.pd_users import User
from etmfa.db.models.pd_user_protocols import PDUserProtocols

@pytest.mark.parametrize(["ai_doc_id", "email_flag", "comment"],
                        [
                            ('8410e658-074a-4c6e-a45d-010d1663a0ca', True, "Email should be sent."),
                            ('8410e658-074a-4c6e-a45d-010d1663a0c-no', False, "Email should not be sent as the entry for aidocid is not present in alert table."),
                        ])
def test_email(new_app_context, ai_doc_id, email_flag, comment):
    _, _app_context = new_app_context
    with _app_context:
        try:
            db_data = db_context.session.query(Protocolalert.id,
                                               Protocolalert.protocol,
                                               Protocolalert.aidocId,
                                               PDUserProtocols.userId,
                                               User.username,
                                               User.email).join(PDUserProtocols,
                                                                and_(Protocolalert.aidocId == ai_doc_id,
                                                                     Protocolalert.id == PDUserProtocols.id)).join(
                User, User.username.in_(('q' + PDUserProtocols.userId, 'u' + PDUserProtocols.userId,
                                         PDUserProtocols.userId))).all()

            for row in db_data:
                protocolalert = Protocolalert.query.filter(and_(Protocolalert.aidocId == ai_doc_id, Protocolalert.id == row.id)).first()
                protocolalert.emailSentFlag = False
                protocolalert.emailSentTime = None
                db_context.session.add(protocolalert)
            db_context.session.commit()

            generate_email.SendEmail.send_status_email(ai_doc_id)

            db_data = db_context.session.query(Protocolalert.emailSentFlag,
                                               Protocolalert.emailSentTime).join(PDUserProtocols, and_(Protocolalert.aidocId == ai_doc_id,
                Protocolalert.id == PDUserProtocols.id)).join(User, User.username.in_(
                ('q' + PDUserProtocols.userId, 'u' + PDUserProtocols.userId, PDUserProtocols.userId))).all()

            if email_flag == False:
                assert len(db_data) == 0
            else:
                for row in db_data:
                    assert email_flag == True and row.emailSentFlag == True and row.emailSentTime is not None

            protocolMetadata = db_context.session.query(PDProtocolMetadata).filter(PDProtocolMetadata.id == ai_doc_id).first()

            protocolMetadata.status = 'PROCESS_COMPLETED'
            protocolMetadata.errorCode = None
            protocolMetadata.errorReason = None
            db_context.session.add(protocolMetadata)
            db_context.session.commit()


        except Exception as ex:
            db_context.session.rollback()
            logging.error(ex)