from dataclasses import dataclass

@dataclass
class CompareRequest:
    compareid: str
    base_doc_id: str
    compare_doc_id: str
    base_iqvxml_path: str
    compare_iqvxml_path: str
    request_type: str