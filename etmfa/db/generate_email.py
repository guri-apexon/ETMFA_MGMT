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
from etmfa.server.config import Config
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
        smtp_obj = smtplib.SMTP(config.email_settings['SMTP_HOST'], config.email_settings['SMTP_PORT'])
        smtp_obj.send_message(msg)
        smtp_obj.quit()
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
                body = f"""An alert was generated for protocol # {row.protocol}. You are receiving this alert because you chose to follow this protocol number in the Protocol Digitalization (PD) Library.\n\nPlease sign into the Protocol Digitalization library to view additional information activity at the following link: {Config.PD_UI_LINK}\n\nThis alert notification is triggered when an approved protocol document with the above protocol number has been uploaded and digitized in the PD Library AND that document has an approval date that is later than any of its associated documents, indicating that it is a new approved version of that protocol.\n\nNote:  At this time, alert notifications are not triggered when drafts or legacy versions of this protocol are uploaded and digitized in the PD Library, but may be viewed by signing into the PD library at the above link.\n\nIf you would like to opt out of receiving email notifications for this protocol, please sign into the PD library at the above link, navigate to view all protocols you are following, and turn off the follow action for this protocol."""
                SendEmail.send_email(doc_id=doc_id, email_to=row.email, subject=subject, body=body)

                time_ = datetime.utcnow()

                protocolalert = Protocolalert.query.filter(and_(Protocolalert.aidocId == doc_id, Protocolalert.id == row.id)).first()
                protocolalert.emailSentFlag = True
                protocolalert.timeUpdated = time_
                protocolalert.emailSentTime = time_
                db_context.session.add(protocolalert)

            db_context.session.commit()

        except Exception as ex:
            db_context.session.rollback()
            logger.exception(f"doc_id={doc_id}, message={str(ex.args)}")



