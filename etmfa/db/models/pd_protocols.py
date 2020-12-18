import datetime

from etmfa.db import db_context


class pd_protocols(db_context.Model):
    __tablename__ = "pd_protocols"

    id = db_context.Column(db_context.Integer(), primary_key=True, nullable=False)
    protocol_number = db_context.Column(db_context.String(200))
    protocol_title = db_context.Column(db_context.String(100))
    project_code = db_context.Column(db_context.String(100))
    phase = db_context.Column(db_context.Integer())
    indication = db_context.Column(db_context.String(500))
    protocol_status = db_context.Column(db_context.Integer(), db_context.ForeignKey('pd_protocol_status.id'), nullable=False)
    protocol_version = db_context.Column(db_context.String(100))
    protocol_sponsor = db_context.Column(db_context.Integer(), db_context.ForeignKey('pd_protocol_sponsor.id'), nullable=False)
    is_active = db_context.Column(db_context.Boolean(), default=False)
    created_by = db_context.Column(db_context.String(100))
    created_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    modified_by = db_context.Column(db_context.String(100))
    modified_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
