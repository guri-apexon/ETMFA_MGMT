import datetime

from sqlalchemy import Column, Float, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from etmfa.db.db import db_context, SchemaBase

class QcEditMetric(db_context.Model):
    __tablename__ = "qc_edit_metric"
    doc_id = Column(String,primary_key=True)
    edit_info=Column(JSONB)