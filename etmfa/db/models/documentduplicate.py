from ..db import db_context
import datetime


class Documentduplicate(db_context.Model):
    __tablename__ = "etmfa_document_duplicate"

    id                       = db_context.Column(db_context.String(50))
    fileName                 = db_context.Column(db_context.String(300))
    documentClass            = db_context.Column(db_context.String(300), primary_key=True)
    customer                 = db_context.Column(db_context.String(300), primary_key=True)
    protocol                 = db_context.Column(db_context.String(300), primary_key=True)
    docHash                  = db_context.Column(db_context.String(300), primary_key=True)
    documentFilePath         = db_context.Column(db_context.String(500))
    country                  = db_context.Column(db_context.String(300))
    site                     = db_context.Column(db_context.String(300))
    receivedDate             = db_context.Column(db_context.String(300))
    docDuplicateFlag         = db_context.Column(db_context.Integer())
    documentRejected         = db_context.Column(db_context.Boolean(), default = False)
    timeCreated              = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastUpdated              = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)


    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj

