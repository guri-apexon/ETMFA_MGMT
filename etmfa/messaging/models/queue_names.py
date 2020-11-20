from enum import Enum


class EtmfaQueues(Enum):
    """Enum of Etmfa queue names."""

    TRIAGE = "triage",
    DIGITIZER1 = "digitizer1"
    DIGITIZER2 = "digitizer2"
    EXTRACTION = "extraction",
    FINALIZATION = "finalization",
    # FEEDBACK = "feedback",
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
