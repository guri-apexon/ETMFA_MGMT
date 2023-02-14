"""Etmfa processing status enum."""
from enum import Enum, unique, auto


@unique
class ProcessingStatus(Enum):
    """PD processing status enum capturing percentual progress of a document."""
    PROCESS_STARTED = 0
    PROCESS_COMPLETED = 100

@unique
class QcStatus(Enum):
    """PD Quality Check status"""
    NOT_STARTED = 'QC_NOT_STARTED'
    QC1 = 'QC1'
    QC2 = 'QC2'
    COMPLETED = 'QC_COMPLETED'



@unique
class FeedbackStatus(Enum):
    """Etmfa feedback status enum capturing percentual progress of a document."""
    FEEDBACK_COMPLETED = auto()
