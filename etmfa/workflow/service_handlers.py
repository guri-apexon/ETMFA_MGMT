

from .default_workflows import GENERIC_SERVICE_HANDLER, ERR_IN_SERVICE, GENERIC_DIG_SERVICE_HANDLER
from .messaging.message_handlers import GenericMessageHandler, ErrorMessageHandler, Digitizer2OmopUpdateHandler,\
    TriageMessageHandler, DigitizationGenericMessageHandler, Digitizer1MessageHandler, I2eOmopMessageHandler,\
    Digitizer2CompareHandler, Digitizer2NormSOAHandler,Digitizer2OmopGenerateHandler
from .messaging.models import EtmfaQueues, LegacyQueues


SERVICE_HANDLERS = {
    GENERIC_SERVICE_HANDLER: GenericMessageHandler(),
    GENERIC_DIG_SERVICE_HANDLER: DigitizationGenericMessageHandler(),
    EtmfaQueues.DOCUMENT_PROCESSING_ERROR.value: ErrorMessageHandler(),  # placeholder
    EtmfaQueues.TRIAGE.value: TriageMessageHandler(),
    EtmfaQueues.DIGITIZER1.value: Digitizer1MessageHandler(),
    EtmfaQueues.I2E_OMOP_UPDATE.value: I2eOmopMessageHandler(),
    EtmfaQueues.DIGITIZER2_OMOPUPDATE.value: Digitizer2OmopUpdateHandler(),
    EtmfaQueues.DIGITIZER2_OMOP_GENERATE.value:Digitizer2OmopGenerateHandler(),
    EtmfaQueues.COMPARE.value: Digitizer2CompareHandler(),
    EtmfaQueues.NORM_SOA.value:Digitizer2NormSOAHandler()
    }


class GetServiceHandler():
    def __init__(self, dfs_path):
        self.dfs_path = dfs_path
        self.pd_service_list = [sr.value for sr in LegacyQueues]
        self.init_handler_params()

    def init_handler_params(self):
        for _,handler in SERVICE_HANDLERS.items():
            if isinstance(handler,DigitizationGenericMessageHandler):
                handler.update_dfs_path(self.dfs_path)

    def get_handler(self, service_name):
        if SERVICE_HANDLERS.get(service_name, None):
            return SERVICE_HANDLERS[service_name]
        if service_name not in self.pd_service_list:
            return SERVICE_HANDLERS[GENERIC_SERVICE_HANDLER]
        else:
            return DigitizationGenericMessageHandler()
