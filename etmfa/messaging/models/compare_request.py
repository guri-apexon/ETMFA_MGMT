from dataclasses import dataclass

@dataclass
class CompareRequest:
    compare_id: str
    id1: str
    IQVXMLPath1: str
    id2: str
    IQVXMLPath2: str
    QUEUE_NAME: str