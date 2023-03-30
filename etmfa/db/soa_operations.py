import uuid
import logging
from .models.pd_iqvassessmentrecord_db import Iqvassessmentrecord
from .models.pd_iqvassessmentvisitrecord_db import Iqvassessmentvisitrecord
from .models.pd_iqvvisitrecord_db import Iqvvisitrecord
from flask_restplus import abort
from etmfa.consts import Consts as consts

logger = logging.getLogger(consts.LOGGING_NAME)

JSON_ERROR = 'Json values are not valid: {}'

def add_study_procedure(session, table_props):
    """
    Added study procedure assessment_text
    """
    try:
        new_table_row_index = table_props[0].get('table_row_index')
        table_roi_id = table_props[0].get('table_roi_id')
        row_assessment_text = table_props[0].get('study_procedure').get('value')
        doc_id = table_props[0].get('doc_id') 
        
        insert_row = add_row_study_procedure(doc_id, row_assessment_text, new_table_row_index, table_roi_id)    
        
        sql_update_index = f"UPDATE iqvassessmentrecord_db SET table_row_index = table_row_index + 1 \
            WHERE table_roi_id = '{table_roi_id}' AND table_row_index >= {new_table_row_index}"
        
        session.execute(sql_update_index)
        session.execute(insert_row)
        return True
    except Exception as exc: 
        session.rollback()
        logger.exception(
            f"Exception received while formatting the data [table_roi_id: {table_roi_id}, table_roi_id: {table_roi_id},\
                new_table_row_index: {new_table_row_index}, row_assessment_text: {row_assessment_text}]. Exception: {str(exc)}")    
     

def add_normalized_data_for_study_procedure(session, table_props):
    """
    Add data in normalized soa
    """
    try:
        new_table_row_index = table_props[0].get('table_row_index')
        table_roi_id = table_props[0].get('table_roi_id')
        row_props = table_props[0].get('row_props')
        doc_id = table_props[0].get('doc_id')
        
        sql_update_index = f"Update iqvassessmentvisitrecord_db SET table_row_index = table_row_index + 1 \
            WHERE table_roi_id = '{table_roi_id}' AND table_row_index >= {new_table_row_index}"
        session.execute(sql_update_index)
        
        for data in row_props:
            sql_add_data = f"""INSERT into iqvassessmentvisitrecord_db (id,doc_id,run_id,assessment,\
                assessment_text,cycle_timepoint,day_timepoint,dts,epoch_timepoint,indicator_text,month_timepoint,\
                    pname,"procedure",procedure_text,"ProcessMachineName","ProcessVersion",roi_id,table_row_index,\
                    table_column_index,section,table_link_text,"DocumentSequenceIndex",\
                table_roi_id,table_sequence_index,study_cohort,visit_type,visit_timepoint,week_timepoint,window_timepoint,\
                    year_timepoint,footnote_0,footnote_1,footnote_2,footnote_3, footnote_4, footnote_5,\
            footnote_6,footnote_7,footnote_8,footnote_9 ) VALUES('{uuid.uuid4()}','{doc_id}','','','','',\
                '','','',{data.get('value')},'','','','','','','',{new_table_row_index}, {data.get('table_column_index')},\
                '','',-1,'{table_roi_id}',-1,'','','','','','','','','','','','','','','','')"""
            session.execute(sql_add_data)
        return True
    except Exception as exc:
        session.rollback() 
        logger.exception(
            f"Exception received while formatting the data [table_roi_id: {table_roi_id},\
                new_table_row_index: {new_table_row_index}, row_props: {row_props}]. Exception: {str(exc)}")


def add_study_visit(session, table_props):
    """
    Add study visit in iqvvisitrecord
    """
    new_table_column_index = table_props[0].get('table_column_index')
    table_roi_id = table_props[0].get('table_roi_id')
    study_visit_data = table_props[0].get('study_visit')
    doc_id = table_props[0].get('doc_id')
    try:
        sql_update_index = f"Update iqvvisitrecord_db SET table_column_index = table_column_index + 1\
            WHERE table_roi_id = '{table_roi_id}' AND table_column_index >= {new_table_column_index}"
        session.execute(sql_update_index)
        add_column_study_visit(session, study_visit_data, doc_id, table_roi_id, new_table_column_index)
        return True
    except Exception as exc: 
        session.rollback()
        logger.exception(
            f"Exception received while formatting the data [table_roi_id: {table_roi_id},\
                new_table_column_index: {new_table_column_index}, study_visit_data: {study_visit_data}]. Exception: {str(exc)}")


def add_normalized_data_for_study_visit(session, table_props):
    """
    Add data in normalized soa
    """
    new_table_column_index = table_props[0].get('table_column_index')
    table_roi_id = table_props[0].get('table_roi_id')
    row_props = table_props[0].get('row_props')
    doc_id = table_props[0].get('doc_id', '')
    try:
        sql_update_index = f"Update iqvassessmentvisitrecord_db SET table_column_index = table_column_index + 1\
            WHERE table_roi_id = \'{table_roi_id}\' AND table_column_index >= {new_table_column_index}"
        session.execute(sql_update_index)
        
        for data in row_props:
            new_table_row_index = data.get('table_row_index')
            value = data.get('value')
            sql_add_data = insert_into_normalized_soa(doc_id, new_table_column_index, new_table_row_index, table_roi_id, value)
            session.execute(sql_add_data)
        return True
    except Exception as exc:
        session.rollback() 
        logger.exception(
            f"Exception received while formatting the data [table_roi_id: {table_roi_id},\
                new_table_column_index: {new_table_column_index}, row_props: {row_props}]. Exception: {str(exc)}")

def update_normalized_soa_cell_value(session, table_props, sub_type):
    """
    Update cell value in normalized soa
    """
    table_roi_id = table_props[0].get('table_roi_id')
    new_table_column_index = table_props[0].get('table_column_index')
    new_table_row_index = table_props[0].get('table_row_index')
    value = table_props[0].get("value")
    study_visit_data = table_props[0].get('study_visit')
    timepoint = table_props[0].get("timepoint")
    doc_id = table_props[0].get('doc_id')
    try:
        if sub_type == 'update_cell':
            sql = f"UPDATE iqvassessmentvisitrecord_db SET indicator_text = '{value}'\
                WHERE table_roi_id = \'{table_roi_id}\' and table_column_index = {new_table_column_index}\
                and table_row_index = {new_table_row_index}"
        elif sub_type == 'update_study_procedure':
            sql = f"UPDATE iqvassessmentrecord_db SET assessment_text = '{value}'\
                WHERE table_roi_id = \'{table_roi_id}\' and table_row_index = {new_table_row_index}"
        elif sub_type == 'update_study_visit':
            sql = f"UPDATE iqvvisitrecord_db SET {timepoint} = '{value}'\
                WHERE table_roi_id = \'{table_roi_id}\' and table_column_index = {new_table_column_index}"
        elif sub_type == 'add_cell':
            sql = insert_into_normalized_soa(doc_id, new_table_column_index, new_table_row_index, table_roi_id, value)
        elif sub_type == 'add_study_procedure':
            sql = add_row_study_procedure(doc_id, value, new_table_row_index, table_roi_id)
        elif sub_type == 'add_study_visit':
            add_column_study_visit(session, study_visit_data, doc_id, table_roi_id, new_table_column_index)
            return True
        else:
            return abort(404, JSON_ERROR.format(sub_type))
        session.execute(sql)
        return True
    except Exception as exc: 
        session.rollback()
        logger.exception(
            f"Exception received while formatting the data [table_roi_id: {table_roi_id},\
                new_table_column_index: {new_table_column_index}, new_table_row_index: {new_table_row_index}\
                    value: {value}]. Exception: {str(exc)}")


def delete_normalized_soa_cell_value_by_column(session, table_props):
    table_roi_id = table_props[0].get('table_roi_id', '').strip()
    table_column_index = table_props[0].get('table_column_index', '')
    try: 
        for table_name in [("iqvvisitrecord_db"), ("iqvassessmentvisitrecord_db")]:
            sql = f'Delete from {table_name} where table_roi_id = \'{table_roi_id}\' and "table_column_index" = {table_column_index}'
            session.execute(sql)
        op_code = '-'
        for table_name in [("iqvvisitrecord_db"), ("iqvassessmentvisitrecord_db")]:
            sql = f'Update {table_name} SET "table_column_index" = "table_column_index" {op_code} 1 where "table_column_index" >= {table_column_index} and table_roi_id = \'{table_roi_id}\''
            session.execute(sql)
        return True
    except Exception as exc:
        session.rollback()
        logger.exception(
            f"Exception received while formatting the data [table_roi_id: {table_roi_id},\
                table_column_index: {table_column_index}]. Exception: {str(exc)}")


def delete_normalized_soa_cell_value_by_row(session, table_props):
    table_row_index = table_props[0].get('table_row_index', '').strip()
    table_roi_id = table_props[0].get('table_roi_id', '').strip()
    try:
        for table_name in [("iqvassessmentrecord_db"), ("iqvassessmentvisitrecord_db")]:
            sql = f'Delete from {table_name} where table_roi_id = \'{table_roi_id}\' and table_row_index = {table_row_index}'
            session.execute(sql)
            op_code = '-'
        for table_name in [("iqvassessmentrecord_db"), ("iqvassessmentvisitrecord_db")]:
            sql = f'Update {table_name} SET "table_row_index" = "table_row_index" {op_code} 1  where "table_row_index" > {table_row_index} and table_roi_id = \'{table_roi_id}\''
            session.execute(sql)
        return True
    except Exception as exc:
        session.rollback()
        logger.exception(
            f"Exception received while formatting the data [table_roi_id: {table_roi_id},\
                table_row_index: {table_row_index}]. Exception: {str(exc)}")


def insert_into_normalized_soa(doc_id, new_table_column_index, new_table_row_index, table_roi_id, value):
    """
    Inserts data in iqvassessmentvisitrecord_db
    """
    sql_add_data = f"""INSERT into iqvassessmentvisitrecord_db (id, doc_id, table_column_index, table_row_index,\
                table_roi_id, indicator_text, "DocumentSequenceIndex", table_sequence_index, assessment, assessment_text, cycle_timepoint,\
                day_timepoint, dts, epoch_timepoint, month_timepoint, pname, procedure, procedure_text,\
                "ProcessMachineName", "ProcessVersion", roi_id, section, table_link_text, study_cohort, visit_type, visit_timepoint, week_timepoint,\
                window_timepoint,year_timepoint,footnote_0,footnote_1,footnote_2,footnote_3, footnote_4, footnote_5,\
            footnote_6,footnote_7,footnote_8,footnote_9) VALUES('{uuid.uuid4()}', '{doc_id}', {new_table_column_index}, {new_table_row_index},\
                '{table_roi_id}\', '{value}', -1, -1,'','','','','','','','','','','','','','','','','','','','','','','','','','',\
                '','','','','')"""
    return sql_add_data


def add_row_study_procedure(doc_id, row_assessment_text, new_table_row_index, table_roi_id):
    insert_row = f"""INSERT into iqvassessmentrecord_db (id, doc_id, run_id, assessment,\
            assessment_text, num_visits, dts, pname, "procedure", procedure_text, "ProcessMachineName",\
            "ProcessVersion", roi_id, table_row_index,section,table_link_text,"DocumentSequenceIndex",\
            table_roi_id,table_sequence_index,study_cohort,footnote_0,footnote_1,footnote_2,footnote_3, footnote_4, footnote_5,\
            footnote_6,footnote_7,footnote_8,footnote_9) VALUES('{uuid.uuid4()}','{doc_id}', '', '', '{row_assessment_text}',\
            22,'','','','','','','',{new_table_row_index},'','',-1, '{table_roi_id}',-1,'',\
                 '', '', '', '', '', '', '', '', '', '')"""
    return insert_row


def add_column_study_visit(session, study_visit_data, doc_id, table_roi_id, new_table_column_index):
    for data in study_visit_data:
        timepoint_dict = {
            'visit_timepoint': '','epoch_timepoint': '', 'cycle_timepoint': '', 'day_timepoint': '',
            'week_timepoint': '', 'window_timepoint': '', 'year_timepoint': '', 'month_timepoint': ''
        }
        timepoint_values = ""
        if data.get("timepoint"):
            timepoint_dict[data.get("timepoint")] = data.get('value')
        timepoint_keys = ", ".join(timepoint_dict.keys())
        timepoint_values = ", ".join([f"'{val}'" if val else "''" for val in timepoint_dict.values()])
        insert_column = f"""INSERT into iqvvisitrecord_db (id, doc_id, table_roi_id, table_column_index,\
                {timepoint_keys}, num_assessments, table_sequence_index, run_id, dts, pname, "ProcessMachineName",\
                "ProcessVersion", table_link_text, "DocumentSequenceIndex", "study_cohort", "visit_type",footnote_0,\
                footnote_1,footnote_2,footnote_3, footnote_4, footnote_5, footnote_6,footnote_7,footnote_8,footnote_9)\
                VALUES('{uuid.uuid4()}','{doc_id}','{table_roi_id}', {new_table_column_index},\
                {timepoint_values}, 5, -1, '','','','','','',-1,'','', '','','','','','','','','','')"""
        session.execute(insert_column)
