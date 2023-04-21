import datetime

from etmfa.db import db_context


class ProtocolSummaryEntities(db_context.Model):
    __tablename__ = "pd_protocol_summary_entities"

    aidocId = db_context.Column(db_context.String(50), primary_key=True)
    runId = db_context.Column(db_context.String(50), primary_key=True)
    source = db_context.Column(db_context.String(32), primary_key=True)
    iqvdataSummaryEntities = db_context.Column(db_context.VARCHAR(None))
    isActive = db_context.Column(db_context.Boolean(), default=True)
    timeCreated = db_context.Column(db_context.DateTime(
        timezone=True), default=datetime.datetime.utcnow)
    timeUpdated = db_context.Column(db_context.DateTime(
        timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
