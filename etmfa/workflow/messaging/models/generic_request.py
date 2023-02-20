from dataclasses import dataclass


@dataclass
class GenericRequest:
    id: str
    IQVXMLPath: str
    FeedbackRunId: int
    OutputFilePrefix: str

@dataclass
class CompareRequest:
    id: str
    compare_id1: str
    compare_id2: str

@dataclass
class I2eOmapRequest:
    id: str
    flow_id:str
    flow_name:str
    OMOPPath: str
    IQVXMLPath: str
    FeedbackRunId: int
    OutputFilePrefix: str
    QUEUE_NAME: str


@dataclass
class DIG2OMAPRequest:
    id: str
    flow_id:str
    flow_name:str
    omop_xml_path: str
    FeedbackRunId: int
    OutputFilePrefix: str

@dataclass
class FeedbackRun:
    id: str
    IQVXMLPath: str
    FeedbackJSONPath: str
    FeedbackRunId: int
    OutputFilePrefix: str
    QUEUE_NAME: str

@dataclass
class DocumentRequest:
    id: str
    doc_id: str


@dataclass
class Dig2XMLPathRequest:
   id: str
   doc_id: str
   FeedbackRunId: str
   flow_name: str 
   flow_id: str
   IQVXMLPath:str
   OutputFilePrefix:str

@dataclass
class AnalyzerRequest:
    flow_id:str
    flow_name:str
    id:str
    doc_id:str
    variable_list:list

