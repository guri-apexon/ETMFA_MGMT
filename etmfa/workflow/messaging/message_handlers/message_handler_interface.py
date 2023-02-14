from typing import Dict, List
from abc import ABC, abstractmethod
from ..models import ServiceMessage,CompositeServiceMessage

class MessageHandler(ABC):
    @abstractmethod
    def on_msg(self,service_name:str, message: ServiceMessage):
        """
        incoming message after completion 
        """
        pass

    @abstractmethod
    def on_input_message_adapter(self,service_name,message: any) -> ServiceMessage:
        """
        incoming message after completion that must be converted to standard
        """
        pass

    @abstractmethod
    def on_output_message_adapter(self,service_name:str, message:CompositeServiceMessage) -> Dict:
        pass