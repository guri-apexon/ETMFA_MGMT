from enum import Enum


class EtmfaQueues(Enum):
    """Enum of Etmfa queue names."""

    TRIAGE = "triage",
    DIGITIZER1 = "digitizer1"
    DIGITIZER2 = "digitizer2"
    I2E_OMOP_UPDATE = "i2e_omop_update" # added for i2e omop update
    DIGITIZER2_OMOPUPDATE='digitizer2_omopupdate' # added for i2e omop update
    EXTRACTION = "extraction",
    FINALIZATION = "finalization",
    FEEDBACK = "feedback",
    COMPARE = "digitizer2_compare"
    DOCUMENT_PROCESSING_ERROR = "documentprocessing_error"


    def __init__(self, queue_prefix):
        """Construct queue name enum."""
        self.queue_prefix = queue_prefix

    @property
    def complete(self):
        """Return a complete queue name.

        E.g., EtmfaQueues.Triage.complete corresponds to triage_complete.
        """
        return f'{self.queue_prefix}_complete'

    @property
    def request(self):
        """Return request queue name."""
        return f'{self.queue_prefix}_request'
