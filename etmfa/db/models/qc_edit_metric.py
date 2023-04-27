from sqlalchemy import Column,VARCHAR
from sqlalchemy.dialects.postgresql import JSONB
from etmfa.db.db import db_context

class QcEditMetric(db_context.Model):
    __tablename__ = "qc_edit_metric"
    doc_id = Column(VARCHAR(128),primary_key=True)

    edit_info=Column(JSONB)