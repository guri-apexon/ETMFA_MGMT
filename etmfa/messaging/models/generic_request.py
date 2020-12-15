from dataclasses import dataclass


@dataclass
class GenericRequest:
    id: str
    IQVXMLPath: str


@dataclass
class OmapRequest:
    id: str
    updated_omop_xml_path: str
    IQVXMLPath: str
    dest_queue_name: str


@dataclass
class DIG2OMAPRequest:
    id: str
    omop_xml_path: str

