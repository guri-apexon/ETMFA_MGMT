from ..db import db_context
from sqlalchemy import Sequence, Index
import datetime


class Documentduplicate(db_context.Model):
    __tablename__ = "etmfa_document_duplicate"

    id                       = db_context.Column(db_context.String(50))
    customer                 = db_context.Column(db_context.String(300), primary_key=True)
    protocol                 = db_context.Column(db_context.String(300), primary_key=True)
    doc_hash                 = db_context.Column(db_context.String(300), primary_key=True)
    document_file_path       = db_context.Column(db_context.String(500))
    country                  = db_context.Column(db_context.String(300))
    site                     = db_context.Column(db_context.String(300))
    document_class           = db_context.Column(db_context.String(300))
    received_date            = db_context.Column(db_context.String(300))
    doc_duplicate_flag       = db_context.Column(db_context.Integer())
    document_rejected        = db_context.Column(db_context.Boolean(), default = False)
    time_created             = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_updated             = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)


    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj

    #Index('core_doc', doc_hash, customer, protocol)
    #Index('country_doc', doc_hash, customer, protocol, country)
    #Index('site_doc', doc_hash, customer, protocol, country, site)