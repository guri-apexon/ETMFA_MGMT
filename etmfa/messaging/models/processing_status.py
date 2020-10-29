"""Etmfa processing status enum."""
from enum import Enum, unique, auto


@unique
class ProcessingStatus(Enum):
    """Etmfa processing status enum capturing percentual progress of a document."""
    TRIAGE_STARTED = 0
    DIGITIZER1_STARTED = 30
    DIGITIZER2_STARTED = 50
    # CLASSIFICATION_STARTED = 00
    EXTRACTION_STARTED = 70
    # FINALIZATION_STARTED = 90
    PROCESS_COMPLETED = 100


@unique
class FeedbackStatus(Enum):
    """Etmfa feedback status enum capturing percentual progress of a document."""
    FEEDBACK_COMPLETED = auto()
