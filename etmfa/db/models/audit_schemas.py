from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, VARCHAR, TEXT
from sqlalchemy.dialects.postgresql import HSTORE
AuditBase = declarative_base()

class AuditParagraphDb(AuditBase):
    __tablename__ = "documentparagraphs_db"
    __table_args__ = {'schema': 'audit'}
    id = Column(VARCHAR(128), primary_key=True, nullable=False)
    hierarchy = Column(VARCHAR(128), nullable=False)
    action = Column(TEXT)
    changed_fields = Column(HSTORE)


class AuditTablesDb(AuditBase):
    __tablename__ = "documenttables_db"
    __table_args__ = {'schema': 'audit'}
    id = Column(VARCHAR(128), primary_key=True, nullable=False)
    hierarchy = Column(VARCHAR(128), nullable=False)
    action = Column(TEXT)
    changed_fields = Column(HSTORE)
