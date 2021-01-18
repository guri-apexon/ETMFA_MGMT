from dataclasses import dataclass


@dataclass
class GenericRequest:
    id: str
    IQVXMLPath: str


@dataclass
class OmapRequest:
    id: str
    OMOPPath: str
    IQVXMLPath: str
    QUEUE_NAME: str


@dataclass
class DIG2OMAPRequest:
    id: str
    omop_xml_path: str

@dataclass
class CompareRequest:
    id: str
    IQVXMLPath: str
    protocol: str


