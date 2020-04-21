from dataclasses import dataclass


@dataclass
class GenericRequest:
    id: str
    IQVXMLPath: str
