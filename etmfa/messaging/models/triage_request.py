from dataclasses import dataclass


@dataclass
class TriageRequest:
    id: str
    filepath: str
    sourceFileName: str
    version_number: str
    protocol: str
    document_status: str
    environment: str
    source_system: str
    sponsor: str
    study_status: str
    amendment_number: str
    project_id: str
    indication: str
    molecule_device: str
    user_id: str
    FeedbackRunId: int
