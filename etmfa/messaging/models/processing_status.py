"""Etmfa processing status enum."""
from enum import Enum, unique, auto


@unique
class ProcessingStatus(Enum):
    """PD processing status enum capturing percentual progress of a document."""
    TRIAGE_STARTED = 0
    DIGITIZER1_STARTED = 15
    DIGITIZER2_STARTED = 30
    I2E_OMOP_UPDATE_STARTED = 45 # added for i2e omop update
    DIGITIZER2_OMOPUPDATE_STARTED= 60 # added for i2e omop update
    EXTRACTION_STARTED = 75
    FINALIZATION_STARTED = 95
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
