import datetime

from etmfa.db import db_context


class Documentcompare(db_context.Model):
    __tablename__ = "pd_protocol_compare"
    compareId = db_context.Column(db_context.String(300), primary_key=True)
    id1 = db_context.Column(db_context.String(300))
    id2 = db_context.Column(db_context.String(300))
    protocolNumber = db_context.Column(db_context.String(45))
    compareIqvXmlPath = db_context.Column(db_context.String(1000))
    compareCSVPath = db_context.Column(db_context.String(1000))
    compareJSONPath = db_context.Column(db_context.String(1000))
    numChangesTotal = db_context.Column(db_context.Integer())
    compareCSVPathNormSOA = db_context.Column(db_context.String(1000))
    compareJSONPathNormSOA = db_context.Column(db_context.String(1000))
    redactProfile = db_context.Column(db_context.String(100))
    feedbackRun = db_context.Column(db_context.Integer())
    swap = db_context.Column(db_context.Boolean(), default = False)
    createdDate = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    updatedDate = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
