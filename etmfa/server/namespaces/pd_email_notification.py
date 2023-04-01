
from etmfa.auth import authenticate
from etmfa.db import db_context 
from etmfa.db.generate_email import send_event_based_mail
from etmfa.server.api import api
from flask_restplus import Resource
from etmfa.consts import Consts as consts
from etmfa.server.namespaces.serializers import notification_args
import logging

logger = logging.getLogger(consts.LOGGING_NAME)

db = db_context.session

ns = api.namespace('PD', path='/v1/documents/notifications',
                   description='notificaion endpoints.')


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