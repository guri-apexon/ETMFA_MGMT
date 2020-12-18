import datetime

from etmfa.db import db_context


class pd_users(db_context.Model):
    __tablename__ = "pd_users"

    user_id = db_context.Column(db_context.Integer(), primary_key=True)
    role_id = db_context.Column(db_context.Integer(), db_context.ForeignKey("pd_roles.id"), nullable=False)
    is_sso_enabled = db_context.Column(db_context.Boolean(), default=False)
    email_id = db_context.Column(db_context.String(256))
    password = db_context.Column(db_context.String(256))
    is_active = db_context.Column(db_context.Boolean(), default=False)
    is_locked = db_context.Column(db_context.Boolean(), default=False)
    created_by = db_context.Column(db_context.String(100))
    created_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    modified_by = db_context.Column(db_context.String(100))
    modified_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
