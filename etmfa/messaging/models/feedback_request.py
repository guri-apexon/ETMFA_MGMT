from dataclasses import dataclass


@dataclass
class FeedbackRequest:
    id: str
    document_file_path: str
    feedback_source: str
    customer: str
    protocol: str
    country: str
    site: str
    document_class: str
    document_date: str
    document_classification: str
    name: str
    language: str
    document_rejected: str
    attribute_auxillary_list: str
