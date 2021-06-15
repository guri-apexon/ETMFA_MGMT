import smtplib
from email.message import EmailMessage
from etmfa.db.db import db_context
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.db.models.pd_users import User
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from sqlalchemy import and_
from datetime import datetime
import logging
from etmfa.consts import Consts as consts
from etmfa.db import config
from etmfa.db.__init__ import received_documentprocessing_error_event
from etmfa.error import ErrorCodes, ManagementException

logger = logging.getLogger(consts.LOGGING_NAME)


class SendEmail:
    @staticmethod
    def send_email(doc_id: str, email_to: str, subject: str, body: str = None):
        if not config.email_settings['EMAILS_ENABLED']:
            logger.error("Sending emails is not enabled!", doc_id=doc_id)
        logger.info(f"Sending status email to {email_to}")
        msg = EmailMessage()
        msg.set_content(subject)
        msg["Subject"] = subject
        msg["To"] = email_to
        msg["From"] = config.email_settings['EMAILS_FROM_EMAIL']
        if body is not None:
            msg.set_content(body)
        s = smtplib.SMTP(config.email_settings['SMTP_HOST'], config.email_settings['SMTP_PORT'])
        s.send_message(msg)
        s.quit()
        extra = {'doc_id': doc_id, 'msg_body': 'Email Sent'}
        logger.info(f'Status email sent to : {email_to}', extra)

    @staticmethod
    def send_status_email(doc_id: str) -> None:
        db_data = db_context.session.query(Protocolalert.id,
                                           Protocolalert.protocol,
                                           Protocolalert.aidocId,
                                           PDUserProtocols.userId,
                                           User.username,
                                           User.email).join(PDUserProtocols, and_(Protocolalert.emailSentFlag == False,
                                                                                  Protocolalert.aidocId == doc_id,
                                                                                  Protocolalert.id == PDUserProtocols.id)).join(
            User, User.username.in_(('q' + PDUserProtocols.userId, 'u' + PDUserProtocols.userId,
                                     PDUserProtocols.userId))).all()


        try:
            for row in db_data:
                subject = f"Protocol Digitization: An alert was generated for protocol # {row.protocol}"
                body = f"""An alert was generated for protocol # {row.protocol}. You can sign into the Protocol Digitalization library to view this activity.\n\nToday, these notifications are provided when when an approved protocol document (determined by protocol number) has been uploaded and digitized in the PD library AND that document has an approval date that is later than any of its associated documents. """
                SendEmail.send_email(doc_id=doc_id, email_to=row.email, subject=subject, body=body)


                time_ = datetime.utcnow()

                protocolalert = Protocolalert.query.filter(and_(Protocolalert.aidocId == doc_id, Protocolalert.id == row.id)).first()
                protocolalert.emailSentFlag = True
                protocolalert.timeUpdated = time_
                protocolalert.emailSentTime = time_
                db_context.session.add(protocolalert)

            ret_val = db_context.session.commit()

        except Exception as ex:
            db_context.session.rollback()
            logger.exception(f"doc_id={doc_id}, message={str(ex.args)}")
            exception = ManagementException(doc_id, ErrorCodes.ERROR_EMAIL_GENERATION)
            received_documentprocessing_error_event(exception.__dict__)



