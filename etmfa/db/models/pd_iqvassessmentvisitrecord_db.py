from sqlalchemy import Column, Table, MetaData, String, Index
from sqlalchemy.dialects.postgresql import VARCHAR
from sqlalchemy.orm import registry
from etmfa.db.db import db_context, SchemaBase
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TEXT,VARCHAR,INTEGER
from dataclasses import dataclass, field
from typing import List
from etmfa.consts import Consts as consts
from etmfa.db.models.pd_iqvassessmentrecord_db import Iqvassessmentrecord
import logging


Base = db_context.make_declarative_base(model=SchemaBase)
mapper_registry = registry()
SchemaBase = declarative_base()
logger = logging.getLogger(consts.LOGGING_NAME)

class IqvassessmentvisitrecordDb(Base):
   __tablename__ = "iqvassessmentvisitrecord_db"
   id = Column(VARCHAR(128),primary_key=True,nullable=False)
   doc_id = Column(TEXT)
   run_id = Column(TEXT)
   assessment = Column(TEXT)
   assessment_text = Column(TEXT)
   cycle_timepoint = Column(TEXT)
   day_timepoint = Column(TEXT)
   dts = Column(TEXT)
   epoch_timepoint = Column(TEXT)
   indicator_text = Column(TEXT)
   month_timepoint = Column(TEXT)
   pname = Column(TEXT)
   procedure = Column(TEXT)
   procedure_text = Column(TEXT)
   ProcessMachineName = Column(TEXT)
   ProcessVersion = Column(TEXT)
   roi_id = Column(TEXT)
   table_row_index = Column(TEXT)
   table_column_index = Column(TEXT)
   section = Column(TEXT)
   table_link_text = Column(TEXT)
   DocumentSequenceIndex = Column(INTEGER, nullable=False)
   table_roi_id = Column(TEXT)
   table_sequence_index = Column(INTEGER)
   study_cohort = Column(TEXT)
   visit_timepoint = Column(TEXT)
   week_timepoint = Column(TEXT)
   window_timepoint = Column(TEXT)
   year_timepoint = Column(TEXT)
   footnote_0 = Column(TEXT)
   footnote_1 = Column(TEXT)
   footnote_2 = Column(TEXT)
   footnote_3 = Column(TEXT)
   footnote_4 = Column(TEXT)
   footnote_5 = Column(TEXT)
   footnote_6 = Column(TEXT)
   footnote_7 = Column(TEXT)
   footnote_8 = Column(TEXT)
   footnote_9 = Column(TEXT)


Index('iqvassessmentvisitrecord_db_doc_id', IqvassessmentvisitrecordDb.doc_id)


@dataclass
class IqvassessmentvisitrecordDbMapper:
    id: str = field(init=False)
    ProcessVersion: str = ''
    ProcessMachineName: str = ''
    pname: str = ''
    doc_id: str = ''
    dts: str = ''
    table_link_text: str = ''
    indicator_text: str = ''
    visit_timepoint: str = ''
    epoch_timepoint: str = ''
    cycle_timepoint: str = ''
    day_timepoint: str = ''
    week_timepoint: str = ''
    window_timepoint: str = ''
    year_timepoint: str = ''
    month_timepoint: str = ''
    roi_id: str = ''
    assessment: str = ''
    section: str = ''
    procedure: str = ''
    assessment_text: str = ''
    procedure_text: str = ''
    footnotes: List = field(default_factory=list)
    marked_record: dict = field(default_factory=dict)


mapper_registry.map_imperatively(IqvassessmentvisitrecordDbMapper, IqvassessmentvisitrecordDb)


class Iqvassessmentvisitrecord():
    def __init__(self, aidoc_id):
        self.aidoc_id = aidoc_id
        
    def get_soatables_mapper(self):
        """
        returns the mapper objects for normSOA tables
        """
        assessment_visitrecord_mapper = None
        try:
            session = db_context.session()
            assessment_visitrecord_mapper = session.query(IqvassessmentvisitrecordDbMapper).filter(
                IqvassessmentvisitrecordDbMapper.doc_id == self.aidoc_id).all()
                    
        except Exception as exc:
            logger.exception(
                f"Exception received for mapper object with [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")

        return assessment_visitrecord_mapper

    def get_footnotes(self, resource_dict):
        """
        Get footnotes and update resource dict
        """
        footnote_list = []
        footnotes = ["footnote_0","footnote_1","footnote_2","footnote_3","footnote_4","footnote_5","footnote_6","footnote_7","footnote_8","footnote_9"]
        try:
            for note in footnotes:
                if note in resource_dict:
                    if resource_dict.get(note):
                        footnote_list.append(resource_dict.get(note))
                    resource_dict.pop(note)
                continue
            resource_dict.update({"footnotes":footnote_list})
            return resource_dict
        except Exception as exc:
            logger.exception(
                f"Exception received for normalized soa data [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")

    def get_fieldsvalue_list(self, resource_dict):
        """
        Appends fieldsvalue in list 
        """
        fieldsvalue_list = []
        try:
            fieldsvalue_list.append(resource_dict.get("day_timepoint")) if len(resource_dict.get("day_timepoint")) != 0 else ''
            fieldsvalue_list.append(resource_dict.get("week_timepoint")) if len(resource_dict.get("week_timepoint")) != 0 else ''
            fieldsvalue_list.append(resource_dict.get("month_timepoint")) if len(resource_dict.get("month_timepoint")) != 0 else ''
            fieldsvalue_list.append(resource_dict.get("year_timepoint")) if len(resource_dict.get("year_timepoint")) != 0 else ''
            fieldsvalue_list.append(resource_dict.get("visit_timepoint")) if len(resource_dict.get("visit_timepoint")) != 0 else ''
            fieldsvalue_list.append(resource_dict.get("epoch_timepoint")) if len(resource_dict.get("epoch_timepoint")) != 0 else ''
            fieldsvalue_list.append(resource_dict.get("cycle_timepoint")) if len(resource_dict.get("cycle_timepoint")) != 0 else ''
            fieldsvalue_list.append(resource_dict.get("window_timepoint")) if len(resource_dict.get("window_timepoint")) != 0 else ''
            return fieldsvalue_list
        except Exception as exc:
            logger.exception(
                f"Exception received for normalized soa data [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")
    
    
    def get_normalized_soa_data(self, assessment_visit_obj, norm_soa, roi_id, footnote):
        """
        Normalized soa
        """
        try:
            for record in assessment_visit_obj:
                resource_dict = {key: value for key, value in record.__dict__.items()}
                resource_dict.pop("_sa_instance_state")
                if resource_dict.get("table_roi_id") == roi_id:
                    if footnote:
                        resource_dict = self.get_footnotes(resource_dict)
                    fieldsvalue_list = self.get_fieldsvalue_list(resource_dict)
                    resource_dict.update({"marked_record":{resource_dict.get("assessment_text"):fieldsvalue_list}})
                    norm_soa.append(resource_dict)
            return norm_soa
        except Exception as exc:
            logger.exception(
                f"Exception received for normalized soa data [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")


    def get_normalized_soa(self, footnote) -> dict:
        """
        Get normalizedsoa records for soa table mapping
        """
        norm_dict = dict()
        try:
            iqvassessment_obj = Iqvassessmentrecord(self.aidoc_id)
            if iqvassessment_obj:
                assessment_visit_obj = self.get_soatables_mapper()
                table_roi_list = iqvassessment_obj.get_tableroi_list()
                if assessment_visit_obj and table_roi_list:
                    for roi_id in table_roi_list:
                        norm_soa = []
                        norm_soa = self.get_normalized_soa_data(assessment_visit_obj, norm_soa, roi_id, footnote)                        
                        norm_dict[roi_id] = norm_soa  
            else:
                logger.error("Error in getting db object.")
                return norm_dict        
        except Exception as exc:
            logger.exception(
                f"Exception received for normalized soa data [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")        
        return  norm_dict


@dataclass
class IqvassessmentvisitrecordDeleteDbMapper:
    id: str = ""
    table_roi_id: str = ""
    table_row_index: int = 0
    table_column_index: int = 0

mapper_registry.map_imperatively(IqvassessmentvisitrecordDeleteDbMapper, IqvassessmentvisitrecordDb)
