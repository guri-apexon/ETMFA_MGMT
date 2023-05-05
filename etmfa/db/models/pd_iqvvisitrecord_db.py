from sqlalchemy import Column, Index
from sqlalchemy.orm import registry
from etmfa.db.db import db_context, SchemaBase
from dataclasses import dataclass, field
from typing import List
from sqlalchemy.dialects.postgresql import TEXT, VARCHAR, INTEGER
from etmfa.consts import Consts as consts
import logging

Base = db_context.make_declarative_base(model=SchemaBase)
mapper_registry = registry()

logger = logging.getLogger(consts.LOGGING_NAME)

class IqvvisitrecordDb(Base):
    __tablename__ = "iqvvisitrecord_db"
    id = Column(VARCHAR(128), primary_key=True, nullable=False)
    doc_id = Column(TEXT)
    run_id = Column(TEXT)
    num_assessments = Column(INTEGER)
    cycle_timepoint = Column(TEXT)
    day_timepoint = Column(TEXT)
    dts = Column(TEXT)
    epoch_timepoint = Column(TEXT)
    indicator_text = Column(TEXT)
    month_timepoint = Column(TEXT)
    pname = Column(TEXT)
    ProcessMachineName = Column(TEXT)
    ProcessVersion = Column(TEXT)
    table_link_text = Column(TEXT)
    table_column_index = Column(TEXT)
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

Index('iqvvisitrecord_db_doc_id', IqvvisitrecordDb.doc_id)


@dataclass
class IqvvisitrecordDbMapper:
    doc_id: str = ''
    visit_timepoint: str = ''
    epoch_timepoint: str = ''
    cycle_timepoint: str = ''
    day_timepoint: str = ''
    week_timepoint: str = ''
    window_timepoint: str = ''
    year_timepoint: str = ''
    month_timepoint: str = ''
    table_roi_id: str = ''


mapper_registry.map_imperatively(IqvvisitrecordDbMapper, IqvvisitrecordDb)


class Iqvvisitrecord():
    def __init__(self, aidoc_id):
        self.aidoc_id = aidoc_id

    def get_soatables_mapper(self):
        """
        returns the mapper objects for nornSOA tables
        """
        visit_record_mapper = None
        try:
            session = db_context.session()
            visit_record_mapper = session.query(IqvvisitrecordDbMapper).filter(
                IqvvisitrecordDbMapper.doc_id == self.aidoc_id).all()

        except Exception as exc:
            logger.exception(
                f"Exception received while mapper object for data [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")

        return visit_record_mapper

    def get_separate_study_visit(self,  roi_list, data) -> dict:
        """
        Study visit: Used to populate headers with respective table id in SOA table.
        """
        try:
            final_data = dict()
            for id in roi_list:
                final_object_list = []
                for key, values in data.items():
                    t_data = [
                        element for element in values if element["table_roi_id"] == id]
                    final_object_list.append({key: t_data})
                final_data[id] = final_object_list
            return final_data
        except Exception as err:
            print("Error in seperating the data: ", err)

    def prepare_study_visit_timepoints(self, visit_dict, timepoint_data) -> dict:
        """
        Prepare data for 8 different timepoints like day, week, month, year, cycle, visit, window, epoch
        """
        try:
            timepoint_dict = dict()
            timepoint_dict['table_row_index'] = 0
            timepoint_dict['table_column_index'] = visit_dict.get(
                'table_column_index')
            timepoint_dict['indicator_text'] = timepoint_data
            timepoint_dict['table_roi_id'] = visit_dict.get('table_roi_id')
            return timepoint_dict
        except Exception as err:
            print("Error in preparing the study visit timepoints: ", err)

    def get_visit_records(self) -> dict:
        """
        Get records from iqvvisitrecord for nornSOA mapping
        """
        cycle_timepoint, day_timepoint, epoch_timepoint, month_timepoint, visit_timepoint, week_timepoint,\
            window_timepoint, year_timepoint = [], [], [], [], [], [], [], []
        visit_dict = dict()
        roi_list = []
        study_visit = dict()

        try:
            visit_obj = self.get_soatables_mapper()

            if visit_obj:
                for record in visit_obj:
                    visit_dict = {key: value for key,
                                  value in record.__dict__.items()}
                    visit_dict.pop("_sa_instance_state")
                    table_roi_id = visit_dict.get("table_roi_id")
                    day_timepoint_data = visit_dict.get("day_timepoint")
                    week_timepoint_data = visit_dict.get("week_timepoint")
                    month_timepoint_data = visit_dict.get("month_timepoint")
                    year_timepoint_data = visit_dict.get("year_timepoint")
                    visit_timepoint_data = visit_dict.get("visit_timepoint")
                    epoch_timepoint_data = visit_dict.get("epoch_timepoint")
                    cycle_timepoint_data = visit_dict.get("cycle_timepoint")
                    window_timepoint_data = visit_dict.get("window_timepoint")

                    if len(day_timepoint_data) != 0 and day_timepoint_data not in day_timepoint and visit_dict.get('day_timepoint'):
                        day_dict_data = self.prepare_study_visit_timepoints(
                            visit_dict, day_timepoint_data)
                        day_timepoint.append(day_dict_data)
                    if len(week_timepoint_data) != 0 and week_timepoint_data not in week_timepoint and visit_dict.get('week_timepoint'):
                        week_dict_data = self.prepare_study_visit_timepoints(
                            visit_dict, week_timepoint_data)
                        week_timepoint.append(week_dict_data)
                    if len(month_timepoint_data) != 0 and month_timepoint_data not in month_timepoint and visit_dict.get('month_timepoint'):
                        month_dict_data = self.prepare_study_visit_timepoints(
                            visit_dict, month_timepoint_data)
                        month_timepoint.append(month_dict_data)
                    if len(year_timepoint_data) != 0 and year_timepoint_data not in year_timepoint and visit_dict.get('year_timepoint'):
                        year_dict_data = self.prepare_study_visit_timepoints(
                            visit_dict, year_timepoint_data)
                        year_timepoint.append(year_dict_data)
                    if len(visit_timepoint_data) != 0 and visit_timepoint_data not in visit_timepoint and visit_dict.get('visit_timepoint'):
                        visit_dict_data = self.prepare_study_visit_timepoints(
                            visit_dict, visit_timepoint_data)
                        visit_timepoint.append(visit_dict_data)
                    if len(epoch_timepoint_data) != 0 and epoch_timepoint_data not in epoch_timepoint and visit_dict.get('epoch_timepoint'):
                        epoch_dict_data = self.prepare_study_visit_timepoints(
                            visit_dict, epoch_timepoint_data)
                        epoch_timepoint.append(epoch_dict_data)
                    if len(cycle_timepoint_data) != 0 and cycle_timepoint_data not in cycle_timepoint and visit_dict.get('cycle_timepoint'):
                        cycle_dict_data = self.prepare_study_visit_timepoints(
                            visit_dict, cycle_timepoint_data)
                        cycle_timepoint.append(cycle_dict_data)
                    if len(window_timepoint_data) != 0 and window_timepoint_data not in window_timepoint and visit_dict.get('window_timepoint'):
                        window_dict_data = self.prepare_study_visit_timepoints(
                            visit_dict, window_timepoint_data)
                        window_timepoint.append(window_dict_data)

                    roi_list.append(table_roi_id)
                    table_data = {
                        "day_timepoint": day_timepoint,
                        "week_timepoint": week_timepoint,
                        "month_timepoint": month_timepoint,
                        "year_timepoint": year_timepoint,
                        "cycle_timepoint": cycle_timepoint,
                        "visit_timepoint": visit_timepoint,
                        "epoch_timepoint": epoch_timepoint,
                        "window_timepoint": window_timepoint
                    }

                study_visit = self.get_separate_study_visit(
                    set(roi_list), table_data)
            else:
                logger.error(f"Error in getting db object.")
            return study_visit
        except Exception as exc:
            logger.exception(
                f"Exception received  for visitdata [aidoc_id: {self.aidoc_id}]. Exception: {str(exc)}")


@dataclass
class IqvvisitrecordDeleteDbMapper:
    id: str = None
    table_column_index: int = None
    table_roi_id: str = None


mapper_registry.map_imperatively(IqvvisitrecordDeleteDbMapper, IqvvisitrecordDb)
