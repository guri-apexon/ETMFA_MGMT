from enum import Enum
from .messaging.models import EtmfaQueues, TERMINATE_NODE


GENERIC_SERVICE_HANDLER = 'generic_service_handler'
GENERIC_DIG_SERVICE_HANDLER = 'generic_dig_service_handler'
ERR_IN_SERVICE = 'err_in_service'


class DWorkFLows(Enum):
    DIGITIZATION = 'digitization'
    META_EXTRACTION = 'meta_extraction'
    FULL_FLOW = 'full_flow'
    DOCUMENT_COMPARE = 'document_compare'
    NORM_SOA_FLOW = 'norm_soa'
    OMOP_GENERATE_FLOW = 'omop_generate'
    LM_FLOW = 'lm_flow'
    PB_FLOW = 'pb_flow'
    ES_INGESTION = 'es_ingestion'


DIG_DGRAPH = [{'service_name': EtmfaQueues.TRIAGE.value, 'depends': []},
              {'service_name': EtmfaQueues.DIGITIZER1.value,
                  'depends': [EtmfaQueues.TRIAGE.value]},
              {'service_name': EtmfaQueues.DIGITIZER2.value,
                  'depends': [EtmfaQueues.DIGITIZER1.value]},
              {'service_name': EtmfaQueues.EXTRACTION.value,
                  'depends': [EtmfaQueues.DIGITIZER2.value]}
              ]

FULL_GRAPH = [{'service_name': EtmfaQueues.TRIAGE.value, 'depends': []},
              {'service_name': EtmfaQueues.DIGITIZER1.value,
                  'depends': [EtmfaQueues.TRIAGE.value]},
              {'service_name': EtmfaQueues.DIGITIZER2.value,
                  'depends': [EtmfaQueues.DIGITIZER1.value]},
              {'service_name': EtmfaQueues.EXTRACTION.value,
                  'depends': [EtmfaQueues.DIGITIZER2.value]},
              {'service_name': EtmfaQueues.DIGITIZER2_OMOP_GENERATE.value,
                  'depends': [EtmfaQueues.EXTRACTION.value]},
              {'service_name': EtmfaQueues.I2E_OMOP_UPDATE.value,
                  'depends': [EtmfaQueues.DIGITIZER2_OMOP_GENERATE.value]},
              {'service_name': EtmfaQueues.DIGITIZER2_OMOPUPDATE.value,
                  'depends': [EtmfaQueues.I2E_OMOP_UPDATE.value]},
              {'service_name': EtmfaQueues.COMPARE.value,
                  'depends': [EtmfaQueues.EXTRACTION.value]},
              {'service_name': EtmfaQueues.META_TAGGING.value,
                  'depends': [EtmfaQueues.DIGITIZER2_OMOPUPDATE.value]},
              {'service_name': EtmfaQueues.META_EXTRACTION.value,
                  'depends': [EtmfaQueues.META_TAGGING.value]},
              {'service_name': EtmfaQueues.PB_ANALYZER.value,
                  'depends': [EtmfaQueues.DIGITIZER2_OMOPUPDATE.value]},
             {'service_name': EtmfaQueues.ES_INGESTION.value, 'depends': [EtmfaQueues.DIGITIZER2_OMOPUPDATE.value]},
              {'service_name': TERMINATE_NODE,'depends': [
                  EtmfaQueues.PB_ANALYZER.value,EtmfaQueues.META_EXTRACTION.value,EtmfaQueues.COMPARE.value,EtmfaQueues.ES_INGESTION.value]}
              ]

META_GRPAH = [{'service_name': EtmfaQueues.META_TAGGING.value, 'depends': []},
              {'service_name': EtmfaQueues.META_EXTRACTION.value,
                  'depends': [EtmfaQueues.META_TAGGING.value]}
              ]

PB_GRAPH=[{'service_name': EtmfaQueues.PB_ANALYZER.value, 'depends': []}]

DOCUMENT_COMPARE_GRAPH = [
    {'service_name': EtmfaQueues.COMPARE.value, 'depends': []},
]

NORM_SOA_GRAPH = [
    {'service_name': EtmfaQueues.NORM_SOA.value, 'depends': []},
]

ES_INGESTION_GRAPH=[
    {'service_name': EtmfaQueues.ES_INGESTION.value, 'depends': []}
]

LM_GRPAH = [
    {'service_name': EtmfaQueues.DIGITIZER2_OMOP_GENERATE.value, 'depends': []},
    {'service_name': EtmfaQueues.I2E_OMOP_UPDATE.value,
        'depends': [EtmfaQueues.DIGITIZER2_OMOP_GENERATE.value]},
    {'service_name': EtmfaQueues.DIGITIZER2_OMOPUPDATE.value,
        'depends': [EtmfaQueues.I2E_OMOP_UPDATE.value]}
]

DEFAULT_WORKFLOWS = {
    DWorkFLows.DIGITIZATION.value: DIG_DGRAPH,
    DWorkFLows.META_EXTRACTION.value: META_GRPAH,
    DWorkFLows.FULL_FLOW.value: FULL_GRAPH,
    DWorkFLows.DOCUMENT_COMPARE.value: DOCUMENT_COMPARE_GRAPH,
    DWorkFLows.NORM_SOA_FLOW.value: NORM_SOA_GRAPH,
    DWorkFLows.LM_FLOW.value: LM_GRPAH,
    DWorkFLows.PB_FLOW.value: PB_GRAPH,
    DWorkFLows.ES_INGESTION.value: ES_INGESTION_GRAPH
}


def get_work_flow_service_map():
    """
    get the dependency for services 
    """
    """
    get the dependency for services 
    """
    service_work_flow_map = {}
    for wf_name, work_flow_info in DEFAULT_WORKFLOWS.items():
        for sr_info in work_flow_info:
            sr_name = sr_info['service_name']
            service_work_flow_map[sr_name] = wf_name
    return service_work_flow_map


DEFAULT_SERVICE_FLOW_MAP = get_work_flow_service_map()
