import datetime

from etmfa.db import db_context


class Documentfeedback(db_context.Model):
    __tablename__ = "etmfa_document_feedback"

    p_id = db_context.Column(db_context.String(50), primary_key=True)
    id = db_context.Column(db_context.String(50))
    userId = db_context.Column(db_context.String(100))
    fileName = db_context.Column(db_context.String(300))
    documentFilePath = db_context.Column(db_context.String(500))
    feedbackSource = db_context.Column(db_context.String(300))
    customer = db_context.Column(db_context.String(300))
    protocol = db_context.Column(db_context.String(300))
    country = db_context.Column(db_context.String(300))
    site = db_context.Column(db_context.String(300))
    documentClass = db_context.Column(db_context.String(300))
    documentDate = db_context.Column(db_context.String(300))
    documentClassification = db_context.Column(db_context.String(300))
    name = db_context.Column(db_context.String(300))
    language = db_context.Column(db_context.String(300))
    documentRejected = db_context.Column(db_context.Boolean(), default=False)
    attributeAuxillaryList = db_context.Column(db_context.String(2000))
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
