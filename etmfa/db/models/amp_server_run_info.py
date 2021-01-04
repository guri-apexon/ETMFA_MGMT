import datetime

from etmfa.db import db_context


class amp_server_run_info(db_context.Model):
    __tablename__ = "amp_server_run_info"

    id = db_context.Column(db_context.String(50), primary_key=True)
    runId = db_context.Column(db_context.String(200))
    aidocId = db_context.Column(db_context.String(256))
    omopXmlPath = db_context.Column(db_context.String(256))
    updatedOmopXmlPath = db_context.Column(db_context.String(256))
    runUrl = db_context.Column(db_context.String(256))
    runStatus = db_context.Column(db_context.String(32))
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    isDeleted = db_context.Column(db_context.Boolean(), default=False)
    deletedOn = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    processTime = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
