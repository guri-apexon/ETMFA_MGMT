import datetime

from etmfa.db import db_context


class pd_protocol_indications(db_context.Model):
    __tablename__ = "pd_protocol_indications"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    indication_name = db_context.Column(db_context.String(100))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
