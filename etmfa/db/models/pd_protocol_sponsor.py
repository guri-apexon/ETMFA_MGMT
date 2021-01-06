import datetime

from etmfa.db import db_context


class PDProtocolSponsor(db_context.Model):
    __tablename__ = "pd_protocol_sponsor"

    sponsorId = db_context.Column(db_context.Integer(), primary_key=True)
    sponsorName = db_context.Column(db_context.String(500))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
