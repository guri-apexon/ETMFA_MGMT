from dataclasses import dataclass
from etmfa.messaging.models.queue_names import EtmfaQueues

@dataclass
class TriageRequest:
    QUEUE_NAME = EtmfaQueues.TRIAGE.request
    
    id: str
    filename: str
    filepath: str
    customer: str
    protocol: str
    country: str
    site: str
    document_class: str
    tmf_ibr: str
    blinded: bool
    tmf_environment: str
    received_date: str
    site_personnel_list: str
    priority: str
    doc_duplicate_flag: str
