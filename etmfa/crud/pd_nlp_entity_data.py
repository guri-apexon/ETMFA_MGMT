import logging

from etmfa.crud.base import CRUDBase
from etmfa.db.models import NlpEntityDb
from etmfa.schemas.pd_nlp_entity_db import NlpEntityCreate, NlpEntityUpdate
from sqlalchemy.orm import Session
from etmfa.consts import Consts as consts
from sqlalchemy import asc

logger = logging.getLogger(consts.LOGGING_NAME)


class NlpEntityCrud(CRUDBase[NlpEntityDb, NlpEntityCreate, NlpEntityUpdate]):
    """
    NLP Entity crud operation to get entity object with clinical terms.
    """
    def get(self, db: Session, doc_id: str, link_id: str):
        try:
            all_term_data = db.query(NlpEntityDb).filter(
                NlpEntityDb.doc_id == doc_id, NlpEntityDb.link_id == link_id,
                NlpEntityDb.hierarchy != 'document').distinct(NlpEntityDb.standard_entity_name,NlpEntityDb.dts).all()

        except Exception as ex:
            all_term_data = []
            logger.exception("Exception in retrieval of data from table", ex)
        return all_term_data

    def get_with_doc_id(self, db: Session, doc_id: str):
        try:
            all_term_data = db.query(NlpEntityDb).filter(
                NlpEntityDb.doc_id == doc_id,NlpEntityDb.standard_entity_name != "",
                NlpEntityDb.hierarchy != 'document').distinct(NlpEntityDb.standard_entity_name,NlpEntityDb.dts).order_by(asc(NlpEntityDb.dts)).all()
        except Exception as ex:
            all_term_data = []
            logger.exception("Exception in retrieval of data from table", ex)
        return all_term_data


nlp_entity_content = NlpEntityCrud(NlpEntityDb)
