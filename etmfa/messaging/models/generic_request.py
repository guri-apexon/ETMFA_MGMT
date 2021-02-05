from dataclasses import dataclass


@dataclass
class GenericRequest:
    id: str
    IQVXMLPath: str

@dataclass
class CompareRequest:
    ID: str
    IQVXML_PATH: str
    PROTOCOL:str

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


