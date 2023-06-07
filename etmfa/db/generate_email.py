import json
import smtplib
from etmfa.db.db import db_context
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.db.models.pd_users import User
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from sqlalchemy import and_
from datetime import datetime, timezone
import logging
from etmfa.consts import Consts as consts
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# added for notification part
from etmfa.db import insert_into_alert_table
from etmfa.consts.constants import EVENT_CONFIG, QC_USER_NOTIFICATION_MESSAGES, DIGITIZER_USER_NOTIFICATION_MESSAGES
from etmfa.db.models.pd_email_templates import PdEmailTemplates
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.db.models.pd_users import User
from flask import Response
from etmfa.server.config import Config
from jinja2 import Template


logger = logging.getLogger(consts.LOGGING_NAME)



def send_mail(subject: str, to_mail: str, html_body_part: str, test_case: bool = False) -> dict:
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
        if not test_case:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
                server.sendmail(Config.FROM_EMAIL, to_mail, message.as_string())
                server.quit()
        logger.info(f"mail sent sucess")
    except Exception as ex:
        logger.exception(f"Exception occured at send mail function {to_mail}, {subject}")
        return {"sent":False}

    return {"sent":True}


def send_event_based_mail(doc_id: str, event, send_mail_flag, test_case=False, user_id_exclude='', db: db_context=None):
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
            'ProtocolTitle': protocol_meta_data.protocolTitle, 'approval_date': str(datetime.today().date()).replace('-',''), "email_template_id":html_record.id}

        insert_into_alert_table(notification_record,event_dict, user_id_exclude,db)
        if send_mail_flag:
            row_data = db.query(PDUserProtocols.id, PDProtocolMetadata.protocol,
                            PDProtocolMetadata.protocolTitle,
                            PDProtocolMetadata.indication,
                            PDProtocolMetadata.status,
                            PDProtocolMetadata.qcStatus,
                            PDProtocolMetadata.versionNumber,
                            PDProtocolMetadata.documentStatus,
                            PDUserProtocols.userId,
                            User.username,
                            User.email).join(PDUserProtocols, and_(PDProtocolMetadata.id == doc_id,
                                                                   PDUserProtocols.follow == True,
                                                                   PDProtocolMetadata.protocol == PDUserProtocols.protocol)).join(
            User, User.username.in_(('q' + PDUserProtocols.userId, 'u' + PDUserProtocols.userId,
                                     PDUserProtocols.userId))).filter_by(**event_dict).all()

        else:
            row_data = []
            
        for row in row_data:
            to_mail = row.email
            username = " ".join(row.email.split("@")[0].split("."))
            doc_link = f"{Config.UI_HOST_NAME}/protocols?protocolId={doc_id}"
            protocol_number = row.protocol
            indication = row.indication
            doc_status = row.documentStatus
            doc_activity = DIGITIZER_USER_NOTIFICATION_MESSAGES.get('PROCESS_COMPLETED') if event == 'NEW_DOCUMENT_VERSION' else DIGITIZER_USER_NOTIFICATION_MESSAGES.get(row.status, 'Digitization Error')
            doc_status_activity = QC_USER_NOTIFICATION_MESSAGES.get(row.qcStatus, 'ERROR')
            version_number = row.versionNumber

            if event_dict.get("qc_complete") or event_dict.get("new_document_version"):
                subject = html_record.subject.format(
                    **{"protocol_number": protocol_number, "doc_status_activity": doc_status})
                html_body = html_record.email_body.format(**{"username": username.title(), "doc_link": doc_link, "protocol_number": row.protocol,
                                                        "indication": indication, "doc_status": doc_status, "doc_activity": doc_activity, "doc_status_activity": doc_status_activity,
                                                        "version_number":version_number})

            elif event_dict.get("edited"):
                subject = html_record.subject
                html_body = html_record.email_body.format(**{"username": username.title(), "doc_link": doc_link, "protocol_number": row.protocol,"version_number":version_number,
                                                        "indication": indication})

            send_mail(subject, to_mail, html_body, test_case)
            logger.info(
                f"docid {doc_id} event {event}  mail sent success for doc_id {doc_id}")
            time_ = datetime.now(timezone.utc)
            db.query(Protocolalert).filter(Protocolalert.id == row.id , Protocolalert.aidocId == doc_id, Protocolalert.protocol == protocol_meta_data.protocol, Protocolalert.email_template_id == html_record.id).update({Protocolalert.emailSentFlag: True,
                                                                                                                                        Protocolalert.timeUpdated: time_, Protocolalert.emailSentTime: time_})
            logger.info(
                f"docid {doc_id} event {event} email sent success and updated protocol alert record for doc_id {doc_id} and protocol {protocol_meta_data.protocol}")
            db.commit()
    except Exception as ex:
        logger.exception(
            f"exception occurend {event} mail send for doc_id {doc_id}")
        return False
    return True


def send_mail_on_edited_event(db: db_context):
    """
        created function for tiggering email for EDITED event
    """
    event = "EDITED"
    doc_ids = [doc_record[0] for doc_record in db.query(Protocolalert).filter(
        Protocolalert.emailSentFlag == False,
        Protocolalert.email_template_id == '3',
        Protocolalert.timeUpdated >= datetime.today().date(),
    ).with_entities(Protocolalert.aidocId).all()]

    event_dict = EVENT_CONFIG.get(event)

    row_data = db.query(PDUserProtocols.id, PDProtocolMetadata.protocol,
                        PDProtocolMetadata.protocolTitle,
                        PDProtocolMetadata.indication,
                        PDProtocolMetadata.status,
                        PDProtocolMetadata.qcStatus,
                        PDProtocolMetadata.versionNumber,
                        PDProtocolMetadata.documentStatus,
                        PDUserProtocols.userId,
                        PDProtocolMetadata.id.label("doc_id"),
                        User.username,
                        User.email).join(PDUserProtocols, and_(PDProtocolMetadata.id.in_(list(set(doc_ids))),
                                                               PDProtocolMetadata.protocol == PDUserProtocols.protocol)).join(
        User, User.username.in_(('q' + PDUserProtocols.userId, 'u' + PDUserProtocols.userId,
                                 PDUserProtocols.userId))).filter_by(**event_dict).all()

    html_record = db.query(PdEmailTemplates).filter(
        PdEmailTemplates.event == event).first()

    subject = html_record.subject
    email_dict = {}
    for row in row_data:
        record = email_dict.get(row.email, [])
        if record:
            email_dict.get(row.email).append({
                "to_mail": row.email,
                "username": " ".join(row.email.split("@")[0].split(".")).title(),
                "doc_link": f"{Config.UI_HOST_NAME}/protocols?protocolId={row.doc_id}",
                "protocol_number": row.protocol,
                "indication": row.indication,
                "doc_status": row.documentStatus,
                "doc_activity": row.status,  
                "version_number": row.versionNumber,
            })
        else:
            email_dict[row.email] = [{
                "to_mail": row.email,
                "username": " ".join(row.email.split("@")[0].split(".")).title(),
                "doc_link": f"{Config.UI_HOST_NAME}/protocols?protocolId={row.doc_id}",
                "protocol_number": row.protocol,
                "indication": row.indication,
                "doc_status": row.documentStatus,
                "doc_activity": row.status,
                "version_number": row.versionNumber,
            }]

        time_ = datetime.now(timezone.utc)
        db.query(Protocolalert).filter(Protocolalert.id == row.id, Protocolalert.aidocId == row.doc_id, Protocolalert.protocol == row.protocol).update({Protocolalert.emailSentFlag: True,
                                                                                                                                                        Protocolalert.timeUpdated: time_, Protocolalert.emailSentTime: time_})
        db.commit()                                                                                                                                               
    # remove duplicate dict in list
    result_dict = {}
    for k, v in email_dict.items():
        new_list = []
        for d in v:
            t = tuple(sorted(d.items()))
            if t not in new_list:
                new_list.append(t)
        result = [dict(t) for t in new_list]
        result_dict[k] = result

    for email, email_val in result_dict.items():
        try:
            html_body = Template(html_record.email_body).render(
                **{"username": email_val[0].get("username"), "email_body": email_val})
            send_mail(subject, email, html_body, False)
            logger.info(
                f"Edit event mail sent success {str(datetime.now())}")
        except Exception as ex:
            logger.exception(
                f"Exception occured to send email exception {ex} on {str(datetime.now())}")
    return {"message":"Email process has been completed successfully"}
