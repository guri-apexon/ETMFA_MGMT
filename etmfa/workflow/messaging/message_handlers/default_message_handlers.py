from typing import Dict, List
from abc import ABC, abstractmethod
from ..models import ServiceMessage, CompositeServiceMessage, ErrorMessage, LegacyErrorMessage
from .message_handler_interface import MessageHandler
from ...db.db_utils import update_doc_processing_status,update_doc_error_status,get_work_flow_name_by_id


class GenericMessageHandler(MessageHandler):

    def on_msg(self, service_name: str, message: ServiceMessage) -> ServiceMessage:
        update_doc_processing_status(
            message.flow_id, service_name,False,message.flow_name)
        return message

    def on_input_message_adapter(self, service_name, message) -> ServiceMessage:
        in_service_message = ServiceMessage(**message)
        return in_service_message

    def on_output_message_adapter(self, service_name: str, message: CompositeServiceMessage):
        for sr_param in message.services_param:
            msg_params = sr_param.params
            if not msg_params.get('docId', None):
                msg_params['docId'] = message.flow_id
        update_doc_processing_status(
            message.flow_id, service_name, True, message.flow_name)
        return message.dict()


class ErrorMessageHandler(MessageHandler):

    def on_msg(self, service_name: str, message: ErrorMessage) -> ErrorMessage:
        update_doc_error_status(message.flow_id,message.flow_name, message.error_code,
                                message.error_message, message.error_message_details)
        return message

    def on_input_message_adapter(self, service_name, message) -> ErrorMessage:
        """
        handle both new and legacy error messages.
        """
        in_service_message = None
        try:
            msg = LegacyErrorMessage(**message)
            work_flow_name=get_work_flow_name_by_id(msg.id)
            in_service_message = ErrorMessage(flow_name=work_flow_name, flow_id=msg.id, service_name=msg.service_name,
                                              error_code=msg.error_code, error_message=msg.error_message, error_message_details=msg.error_message_details)
        except Exception as e:
            pass
        if not in_service_message:
            in_service_message = ErrorMessage(**message)
        return in_service_message

    def on_output_message_adapter(self, service_name: str, message):
        return message
