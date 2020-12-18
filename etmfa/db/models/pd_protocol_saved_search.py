import datetime

from etmfa.db import db_context


class pd_protocol_saved_search(db_context.Model):
    __tablename__ = "pd_protocol_saved_search"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    keyword = db_context.Column(db_context.String(500))
    user = db_context.Column(db_context.String(200))
    timecreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastupdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
