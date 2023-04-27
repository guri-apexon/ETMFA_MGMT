from sqlalchemy import Column,Index
from sqlalchemy.orm import registry
from etmfa.db.db import db_context, SchemaBase
from sqlalchemy.dialects.postgresql import TEXT,VARCHAR,INTEGER
from dataclasses import dataclass
from typing import List
import logging
from etmfa.consts import Consts as consts

Base = db_context.make_declarative_base(model=SchemaBase)
mapper_registry = registry()

logger = logging.getLogger(consts.LOGGING_NAME)

class IqvassessmentrecordDb(Base):
   __tablename__ = "iqvassessmentrecord_db"
   id = Column(VARCHAR(128),primary_key=True,nullable=False)
   doc_id = Column(TEXT)
   run_id = Column(TEXT)
   assessment = Column(TEXT)
   assessment_text = Column(TEXT)
   num_visits = Column(INTEGER)
   dts = Column(TEXT)
   pname = Column(TEXT)
   procedure = Column(TEXT)
   procedure_text = Column(TEXT)
   ProcessMachineName = Column(TEXT)
   ProcessVersion = Column(TEXT)
   roi_id = Column(TEXT)
   table_row_index = Column(TEXT)
   section = Column(TEXT)
   table_link_text = Column(TEXT)
   DocumentSequenceIndex = Column(INTEGER,nullable=False)
   table_roi_id = Column(TEXT)
   table_sequence_index = Column(INTEGER)
   study_cohort = Column(TEXT)
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

Index('iqvassessmentrecord_db_doc_id',IqvassessmentrecordDb.doc_id)


@dataclass
class IqvassessmentrecordDbMapper:
    doc_id: str = None
    assessment_text: str = None
    table_roi_id: str = None
    
mapper_registry.map_imperatively(IqvassessmentrecordDbMapper, IqvassessmentrecordDb)



class Iqvassessmentrecord():
    def __init__(self, aidoc_id):
        self.aidoc_id = aidoc_id
        
    def get_soatables_mapper(self):
        """
        returns the mapper objects for nornSOA tables
        """
        assessment_record_mapper = None
        try:
            session = db_context.session()
            assessment_record_mapper = session.query(IqvassessmentrecordDbMapper).filter(
                IqvassessmentrecordDbMapper.doc_id == self.aidoc_id).all()
        except Exception as exc:
            logger.exception(
                f"Exception received while mapper object for data [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")

        return assessment_record_mapper



    def get_tableroi_list(self) -> set:
        """
        get set of table_roi_id for normSOA mapping
        """
        table_roi = [] 
        try:
            assessment_obj = self.get_soatables_mapper()
            if assessment_obj:
                    for record in assessment_obj:
                        assessment_dict = {key: value for key, value in record.__dict__.items()}
                        table_roi_id = assessment_dict.get("table_roi_id")
                        table_roi.append(table_roi_id) 
                    table_roi_list = set(table_roi)
            else:
                logger.error(f"Error in getting db object.")
                return table_roi_list
        except Exception as exc:
            logger.exception(
                f"Exception received  for assessment table_roi data [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")        
        return table_roi_list 

    def get_assessment_text(self) -> dict:
        """
        get all assessment texts corresponding to table_roi_id for normSOA mapping
        """ 
        study_procedures = dict()      
        try:
            assessment_obj = self.get_soatables_mapper()
            table_roi_list = self.get_tableroi_list()
            if assessment_obj and table_roi_list:
                for roi_id in  list(table_roi_list):
                    assessment_list = []
                    for record in assessment_obj:
                        assessment_dict = {key: value for key, value in record.__dict__.items()} 
                        if assessment_dict.get("table_roi_id") == roi_id:
                            study_procedure_dict = dict()
                            assessment_text = assessment_dict.get('assessment_text')
                            study_procedure_dict['table_row_index'] = assessment_dict.get('table_row_index')
                            study_procedure_dict['table_column_index'] = 0
                            study_procedure_dict['indicator_text'] = assessment_text
                            assessment_list.append(study_procedure_dict)
                    study_procedures[roi_id] = assessment_list
            else:
                logger.error(f"Error in getting db object or table ids.")
        except Exception as exc:
            logger.exception(
                f"Exception received  for assessment_text data [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")        
        return study_procedures
