
from typing import Dict
from ..models import ServiceMessage,CompositeServiceMessage,ServiceInfo
from .message_handler_interface import MessageHandler


class ServiceMessageHandler():
    def __init__(self,service_handeler_callback,logger):
        self.get_service_handler=service_handeler_callback
        self.logger=logger

    def create_start_message(self, service_name, queue_name, flow_name, flow_id,service_param):
        service_msg = ServiceMessage(flow_name=flow_name, flow_id=flow_id, params=service_param)
        sr_info = ServiceInfo(service_name=service_name,
                              params=service_msg.params)
        comp_msg = CompositeServiceMessage(
            flow_name=flow_name, flow_id=flow_id, services_param=[sr_info])
        comp_msg.services_param = [sr_info]
        return comp_msg


    def on_input_message_adapter(self, msg_obj, service_name):
        handler = self.get_service_handler(service_name)
        return handler.on_input_message_adapter(service_name,msg_obj)

    def on_msg(self, msg_obj, service_name,meta_info={}) -> ServiceMessage:
        """
        do db update for status.
        validate for message type,Do mapping w.r.t function and pass forward.

        """
        handler = self.get_service_handler(service_name)
        out_obj = handler.on_msg(service_name,msg_obj)
        return out_obj

    def on_output_message_adapter(self,next_services_with_msg_obj: Dict[str, CompositeServiceMessage]):
        """
        if any handler return None ,add that service to skipped services and do finish task on those
        """
        next_services_mod_obj,skipped_services_msg_obj_map={},{}
        for service_name,comp_msg_obj in next_services_with_msg_obj.items():
            handler = self.get_service_handler(service_name)
            msg_obj= handler.on_output_message_adapter(service_name, comp_msg_obj)
            if msg_obj:
                next_services_mod_obj[service_name]=msg_obj
            else:
                common_params={}
                for sr_info in comp_msg_obj.services_param:
                    common_params.update(sr_info.params)
                service_msg=ServiceMessage(flow_name=comp_msg_obj.flow_name,flow_id=comp_msg_obj.flow_id,params=common_params)
                skipped_services_msg_obj_map[service_name]=service_msg.__dict__
        return next_services_mod_obj,skipped_services_msg_obj_map
       