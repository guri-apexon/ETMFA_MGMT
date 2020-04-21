"""Etmfa processing status enum."""
from enum import Enum

class ProcessingStatus(Enum):
    """Etmfa processing status enum capturing percentual progress of a document."""
    TRIAGE_STARTED = 0
    OCR_STARTED = 30
    CLASSIFICATION_STARTED = 70
    ATTRIBUTEEXTRACTION_STARTED = 80
    FINALIZATION_STARTED = 90
    PROCESS_COMPLETED = 100
    FEEDBACK_COMPLETED = 100
