from enum import Enum


class DocumentClass(Enum):
    """PD DocumentStatus enum capturing the status of a document."""
    FINAL = "final"
    DRAFT = "draft"

    # STUDY = "study"
