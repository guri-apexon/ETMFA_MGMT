from ..db import db_context
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Sequence
#from ..status import StatusEnum
import datetime


class Documentfeedback(db_context.Model):
    __tablename__ = "etmfa_document_feedback"


    p_id                     = db_context.Column(db_context.String(50), primary_key=True)
    id                       = db_context.Column(db_context.String(50))
    document_file_path       = db_context.Column(db_context.String(300))
    feedback_source          = db_context.Column(db_context.String(100))
    customer                 = db_context.Column(db_context.String(300))
    protocol                 = db_context.Column(db_context.String(300))
    country                  = db_context.Column(db_context.String(300))
    site                     = db_context.Column(db_context.String(300))
    document_class           = db_context.Column(db_context.String(300))
    document_date            = db_context.Column(db_context.String(50))
    document_classification  = db_context.Column(db_context.String(100))
    name                     = db_context.Column(db_context.String(300))
    language                 = db_context.Column(db_context.String(3))
    document_rejected        = db_context.Column(db_context.String(1))
    attribute_auxillary_list = db_context.Column(db_context.String(2000))
    #time_created            = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_updated             = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)


    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj

