from enum import Enum


class DocumentClass(Enum):
    """PD DocumentStatus enum capturing the status of a document."""
    ACTIVE = "active"
    FINAL = "final"
    DRAFT = "draft"

    # STUDY = "study"
