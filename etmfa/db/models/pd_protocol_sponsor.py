import datetime

from etmfa.db import db_context


class pd_protocol_sponsor(db_context.Model):
    __tablename__ = "pd_protocol_sponsor"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    sponsor_name = db_context.Column(db_context.String(500))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
