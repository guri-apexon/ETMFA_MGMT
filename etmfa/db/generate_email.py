import json
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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# added for notification part
from etmfa.db import insert_into_alert_table
from etmfa.consts.constants import EVENT_CONFIG
from etmfa.db.models.pd_email_templates import PdEmailTemplates
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.db.models.pd_users import User
from flask import Response
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



def send_mail(subject: str, to_mail: str, html_body_part: str) -> dict:
    """
    this function send mail with html content attached to email body
    """
    try:
        message = MIMEMultipart("alternative")
        message['From'] = Config.FROM_EMAIL
        message['To'] = to_mail
        message['Subject'] = subject
        part = MIMEText(html_body_part, "html")
        message.attach(part)
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.sendmail(Config.FROM_EMAIL, to_mail, message.as_string())
            server.quit()
        logger.info(f"mail sent sucess")
    except Exception as ex:
        logger.exception(f"Exception occured at send mail function {to_mail}, {subject}")
        return {"sent":False}

    return {"sent":True}


def send_event_based_mail(db: db_context, doc_id: str, event):
    """
    send email based on event and update email sent time and sent flag in protocol alert table 
    :param db: DB instance
    :param doc_id: document id
    :event: document related event example QC complete, Digitization Complete...
    """
    try:
        # verify event present or not  
        event_dict = EVENT_CONFIG.get(event)
        if not event_dict:
            message = json.dumps(
            {'message': "Provided event does not exists"})
            return Response(message, status=400, mimetype='application/json')

        html_record = db.query(PdEmailTemplates).filter(
            PdEmailTemplates.event == event).first()
        protocol_meta_data = db.query(PDProtocolMetadata).filter(
            PDProtocolMetadata.id == doc_id).first()
        notification_record = {'AiDocId': doc_id, 'ProtocolNo': protocol_meta_data.protocol,
            'ProtocolTitle': protocol_meta_data.protocolTitle, 'approval_date': str(datetime.today().date()).replace('-','')}

        insert_into_alert_table(notification_record,event_dict)
        row_data = db.query(PDUserProtocols.id, PDProtocolMetadata.protocol,
                            PDProtocolMetadata.protocolTitle,
                            PDProtocolMetadata.indication,
                            PDProtocolMetadata.status,
                            PDProtocolMetadata.qcStatus,
                            PDProtocolMetadata.documentStatus,
                            PDUserProtocols.userId,
                            User.username,
                            User.email).join(PDUserProtocols, and_(PDProtocolMetadata.id == doc_id,
                                                                   PDProtocolMetadata.protocol == PDUserProtocols.protocol)).join(
            User, User.username.in_(('q' + PDUserProtocols.userId, 'u' + PDUserProtocols.userId,
                                     PDUserProtocols.userId))).filter_by(**event_dict).all()

        for row in row_data:
            to_mail = row.email
            username = " ".join(row.email.split("@")[0].split("."))
            doc_link = f"{Config.UI_HOST_NAME}/protocols?protocolId={doc_id}"
            protocol_number = row.protocol
            indication = row.indication
            doc_status = row.documentStatus
            doc_activity = row.status
            doc_status_activity = row.qcStatus
            subject = html_record.subject.format(
                **{"protocol_number": protocol_number, "doc_status_activity": doc_status_activity})
            html_body = html_record.email_body.format(**{"username": username, "doc_link": doc_link, "protocol_number": row.protocol,
                                                      "indication": indication, "doc_status": doc_status, "doc_activity": doc_activity, "doc_status_activity": doc_status_activity})

            send_mail(subject, to_mail, html_body)
            logger.info(
                f"docid {doc_id} event {event}  mail sent success for doc_id {doc_id}")
            time_ = datetime.utcnow()
            db.query(Protocolalert).filter(Protocolalert.id == row.id , Protocolalert.aidocId == doc_id, Protocolalert.protocol == protocol_meta_data.protocol).update({Protocolalert.emailSentFlag: True,
                                                                                                                                        Protocolalert.timeUpdated: time_, Protocolalert.emailSentTime: time_})
            logger.info(
                f"docid {doc_id} event {event} email sent success and updated protocol alert record for doc_id {doc_id} and protocol {protocol_meta_data.protocol}")
            db.commit()
    except Exception as ex:
        logger.exception(
            f"exception occurend {event} mail send for doc_id {doc_id}")
        return False
    return True