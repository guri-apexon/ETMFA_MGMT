import datetime

from etmfa.db import db_context


class pd_user_protocols(db_context.Model):
    __tablename__ = "pd_user_protocols"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    protocol_id = db_context.Column(db_context.Integer(), db_context.ForeignKey("pd_protocols.id"))
    user_id = db_context.Column(db_context.Integer(), db_context.ForeignKey("pd_users.user_id"))
    is_active = db_context.Column(db_context.Boolean(), default=False)
    created_by = db_context.Column(db_context.String(100))
    created_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    modified_by = db_context.Column(db_context.String(100))
    modified_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
