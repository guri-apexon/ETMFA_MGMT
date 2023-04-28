import time
import re
import numpy as np
from sqlalchemy import text
from multiprocessing import Process
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from etmfa.db.models.qc_edit_metric import QcEditMetric
from etmfa_core.postgres_db_schema import DocumentparagraphsDb, DocumenttablesDb
from etmfa.db.models.audit_schemas import AuditParagraphDb, AuditTablesDb
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from ..config import Config
from etmfa.consts.constants import QcStatus
from sqlalchemy.ext.declarative import declarative_base
from etmfa.db.db import db_context
from datetime import datetime, timedelta
import logging
from etmfa.consts import Consts
import json
from ...workflow.exceptions import SendExceptionMessages

logger = logging.getLogger(Consts.LOGGING_NAME)


def get_confidence_metric_stats(session, doc_ids):
    """function to calculate confidence score """
    try:
        all_data = session.query(QcEditMetric).filter(
            QcEditMetric.doc_id.in_(doc_ids)).all()
        total_changes_per_page = 0
        if len(all_data) == 0:
            return {'confidence_score': 0, "Message": "Data doesn't exist for provided"
                                                      " input param"}
        for data in all_data:
            info = data.edit_info
            num_pages = info["num_pages"]
            num_changes = info["tbl_mod_tokens"] + info["text_mod_tokens"] + info["tbl_insert_tokens"] + \
                          info["text_insert_tokens"] + info["num_image_update"]
            changes_per_page = num_changes / num_pages
            total_changes_per_page += changes_per_page
        avg_changes_per_page = total_changes_per_page / len(all_data)
        confidence_score = np.exp(-(avg_changes_per_page / 10))
        confidence_score = 0.2 if confidence_score < 0.2 else confidence_score
        result = {'confidence_score': int(confidence_score * 100), "Message": "Success"}

        return result
    except Exception as e:
        raise SendExceptionMessages(
            f'Unable to calculate confidence score. Reason: {str(e)}')


def fetch_records_from_db(sponsor_name=None, doc_status=None, doc_id=None):
    """Function to fetch records based on sponsorname or doc_id from Database"""
    try:
        session = db_context.session()
        if not doc_id:
            result = session.query(PDProtocolMetadata.id)
            if sponsor_name:
                result=result.filter(PDProtocolMetadata.sponsor == sponsor_name)
            if doc_status:
                result = result.filter(PDProtocolMetadata.documentStatus == doc_status)
            doc_ids = [i[0] for i in result]
        else:
            doc_ids = [doc_id]
        confidence_score = get_confidence_metric_stats(session, doc_ids)
        return confidence_score
    except Exception as e:
        raise SendExceptionMessages(
            f'Unable to calculate confidence score. Reason: {str(e)}')



class ConfidenceMatrix():
    def __init__(self):
        self.session_local = None
        self.custom_ids = None
        self.time_stamp_id = "".join(['1'] * 8)

    def add_custom_ids(self, ids):
        self.custom_ids = ids

    def add_engine_context(self):
        """methond to add sql engine """
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI,
                               pool_pre_ping=True, pool_size=1, max_overflow=-1, echo=False)
        self.session_local = sessionmaker(
            autocommit=False, autoflush=False, bind=engine)

    def get_num_pages(self, session, doc_id):
        """ Fetch number of pages from database"""

        doc_obj = session.query(DocumentparagraphsDb.PageSequenceIndex).filter(DocumentparagraphsDb.doc_id == doc_id). \
            order_by(DocumentparagraphsDb.PageSequenceIndex.desc()).first()
        return doc_obj[0] if doc_obj else None

    def get_tbl_changes(self, session, doc_id, tbl, audit_tbl, prefix):
        """ fetch table changes from database"""
        mod_info_list = session.query(tbl.id, tbl.num_updates, tbl.Value, tbl.SequenceID).filter(tbl.doc_id == doc_id,
                                                                                                 tbl.Value != '',
                                                                                                 tbl.userId != None,
                                                                                                 ).all()
        total_mod_tokens, total_insert_tokens, total_num_insert, total_num_updates = 0, 0, 0, 0

        for mod_info in mod_info_list:
            cid = mod_info[0]
            tokens = re.split('\W+', mod_info[2])
            num_tokens = len(tokens)
            is_insert = session.query(audit_tbl.id).filter(
                audit_tbl.id == cid, audit_tbl.action == 'I').first()
            if is_insert:
                total_num_insert += 1
                total_insert_tokens += num_tokens
            else:
                total_num_updates += 1
                total_mod_tokens += num_tokens

        return {f'{prefix}_mod_tokens': total_mod_tokens,
                f'{prefix}_insert_tokens': total_insert_tokens,
                f'{prefix}_num_insert': total_num_insert,
                f'{prefix}_num_updates': total_num_updates}

    def get_image_changes(self, session, doc_id):
        mod_ids = session.query(DocumentparagraphsDb.id).filter(DocumentparagraphsDb.doc_id == doc_id,
                                                                DocumentparagraphsDb.m_ROI_TYPEVal == 100,
                                                                DocumentparagraphsDb.userId != None,
                                                                ).all()
        return len(mod_ids)

    def get_latest_doc_ids(self, session, last_timestamp):
        reviewed_docs = session.query(PDProtocolMetadata.id).filter(
            PDProtocolMetadata.qcStatus == QcStatus.COMPLETED.value,
            PDProtocolMetadata.lastUpdated >= last_timestamp).all()
        return [doc[0] for doc in reviewed_docs]

    def get_last_run_timestamp(self, session):
        info = session.query(QcEditMetric).filter(QcEditMetric.doc_id == self.time_stamp_id).first()
        ctime=None
        if info:
            last_run_timestamp=info.edit_info['last_run_timestamp']
            ctime=datetime.strptime(last_run_timestamp,'%Y-%m-%d %H:%M:%S.%f')
        return datetime.utcnow() - timedelta(days=365 * 20) if not ctime else ctime

    def update_last_run_timestamp(self, session,curr_time_stamp):
        info = session.query(QcEditMetric).filter(QcEditMetric.doc_id == self.time_stamp_id).first()
        if not info:
            info = QcEditMetric()
            info.doc_id = self.time_stamp_id
        info.edit_info = {'last_run_timestamp': str(curr_time_stamp)}
        session.add(info)
        session.commit()

    def run(self):
        """ Handler to run process ConfidenceMatrix """
        self.add_engine_context()
        with self.session_local() as session:
            logger.info('updating information of num of edits for latest documents')

            last_start_timestamp=datetime.utcnow()
            last_run_timestamp = self.get_last_run_timestamp(session)
            doc_ids = self.get_latest_doc_ids(session, last_run_timestamp)
            doc_ids = self.custom_ids if self.custom_ids else doc_ids
            for doc_id in doc_ids:
                num_pages = self.get_num_pages(session, doc_id)
                if not num_pages:
                    continue
                logger.info(f'updating info for {doc_id}')
                num_image_changes = self.get_image_changes(session, doc_id)
                para_info = self.get_tbl_changes(
                    session, doc_id, DocumentparagraphsDb, AuditParagraphDb, 'text')
                tbl_info = self.get_tbl_changes(
                    session, doc_id, DocumenttablesDb, AuditTablesDb, 'tbl')
                data = {'num_pages': num_pages,
                        'num_image_update': num_image_changes}
                data.update(para_info)
                data.update(tbl_info)
                qc_metric = QcEditMetric()
                prev_data = session.query(QcEditMetric).filter(
                    QcEditMetric.doc_id == doc_id).first()
                if prev_data:
                    prev_data.edit_info = data
                else:
                    qc_metric.doc_id = doc_id
                    qc_metric.edit_info = data
                    session.add(qc_metric)
                session.commit()
            self.update_last_run_timestamp(session,last_start_timestamp)
            logger.info('edit info updated for all recent documents ')


class ConfidenceMatrixRunner(Process):
    """This class works as a scheduler to calculate confidence score & store it in DB"""

    def __init__(self, run_interval_in_hrs=24):
        Process.__init__(self)
        self.daemon=True
        self.last_update_time = time.time()
        self.first_run = True
        self.run_interval_in_hrs = run_interval_in_hrs
        self.cm = None

    def run(self, custom_ids=None):
        while(True):
            time_diff_hrs = (time.time() - self.last_update_time) / 3600
            logger.info('confidence scores process lookup ')
            if time_diff_hrs >= self.run_interval_in_hrs or self.first_run:
                logger.info("running confidence matrix runner")
                self.cm = ConfidenceMatrix()
                self.cm.add_custom_ids(custom_ids)
                self.cm.run()
                self.last_update_time = time.time()
                self.first_run = False
                logger.info('confidence scores calculated')
            if custom_ids:
                break
            time.sleep(1800)
