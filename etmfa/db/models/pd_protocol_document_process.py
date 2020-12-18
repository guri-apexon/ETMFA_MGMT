import datetime

from etmfa.db import db_context


class pd_protocol_document_process(db_context.Model):
    __tablename__ = "pd_protocol_document_process"

    id = db_context.Column(db_context.String(200), primary_key=True)
    userid = db_context.Column(db_context.String(50))
    isprocessing = db_context.Column(db_context.Boolean(), default=False)
    filename = db_context.Column(db_context.String(300))
    documentfilepath = db_context.Column(db_context.String(500))
    percentcomplete = db_context.Column(db_context.String(100))
    status = db_context.Column(db_context.String(100))
    feedback = db_context.Column(db_context.String(100))
    errorcode = db_context.Column(db_context.Integer())
    errorreason = db_context.Column(db_context.String(100))
    timecreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastupdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
