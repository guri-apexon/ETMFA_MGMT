import datetime

from etmfa.db import db_context


class pd_protocol_status(db_context.Model):
    __tablename__ = "pd_protocol_status"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    protocol_status = db_context.Column(db_context.String(100))
    protocol_status_description = db_context.Column(db_context.String(1000))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
