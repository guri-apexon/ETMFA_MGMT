from dataclasses import dataclass


@dataclass
class TriageRequest:
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
    userId: str
    doc_duplicate_flag: str
