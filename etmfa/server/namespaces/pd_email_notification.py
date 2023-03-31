import datetime
import json
import logging
from sqlalchemy import and_
from etmfa.auth import authenticate
from etmfa.consts.constants import EVENT_CONFIG
from etmfa.db import db_context, insert_into_alert_table
from etmfa.db.generate_email import send_mail
from etmfa.db.models.pd_email_templates import PdEmailTemplates
from etmfa.db.models.pd_protocol_alert import Protocolalert
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_user_protocols import PDUserProtocols
from etmfa.db.models.pd_users import User
from etmfa.server.api import api
from flask_restplus import Resource
from etmfa.consts import Consts as consts
from etmfa.server.namespaces.serializers import notification_args
from flask import Response
from etmfa.server.config import Config 

logger = logging.getLogger(consts.LOGGING_NAME)

db = db_context.session

ns = api.namespace('PD', path='/v1/documents/notifications',
                   description='notificaion endpoints.')

def send_event_based_mail(db: db_context, doc_id: str, event):
    """
    send email based on event and update email sent time and sent flag in protocol alert table 
    :param db: DB instance
    :param doc_id: document id
    :event: document related event example QC complete, Digitization Complete...
    """
    try:
        # create a reord on pdalert table

        html_record = db.query(PdEmailTemplates).filter(
            PdEmailTemplates.event == event).first()
        protocol_meta_data = db.query(PDProtocolMetadata).filter(
            PDProtocolMetadata.id == doc_id).first()
        notification_record = {'AiDocId': doc_id, 'ProtocolNo': protocol_meta_data.protocol,
            'ProtocolTitle': protocol_meta_data.protocolTitle, 'approval_date': str(datetime.datetime.today().date()).replace('-','')}
        
        event_dict = EVENT_CONFIG.get(event)
        if not event_dict:
            message = json.dumps(
            {'message': "Provided event does not exists"})
            return Response(message, status=400, mimetype='application/json')

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
            time_ = datetime.datetime.utcnow()
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


@ns.route("/send/email")
@ns.response(500, 'Server error.')
class SendNotifications(Resource):
    @ns.expect(notification_args)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Notification issue')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """
        Send notification emails
        """
        args = notification_args.parse_args()
        doc_id = args.get('doc_id', '')
        event = args.get('event', '')
        response = send_event_based_mail(db, doc_id, event)
        return response