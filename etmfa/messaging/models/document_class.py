from enum import Enum


class DocumentClass(Enum):
    """Etmfa DocumentClass enum capturing the document class of a document."""
    CORE = "core"
    COUNTRY = "country"
    SITE = "site"
    STUDY = "study"
