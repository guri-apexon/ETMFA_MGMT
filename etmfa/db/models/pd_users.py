import datetime

from etmfa.db import db_context


class PDUsers(db_context.Model):
    __tablename__ = "pd_users"

    userId = db_context.Column(db_context.String(50), primary_key=True)
    roleId = db_context.Column(db_context.String(50), primary_key=True)
    isSsoEnabled = db_context.Column(db_context.Boolean(), default=False)
    emailId = db_context.Column(db_context.String(256))
    password = db_context.Column(db_context.String(256))
    isActive = db_context.Column(db_context.Boolean(), default=False)
    isLocked = db_context.Column(db_context.Boolean(), default=False)
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    userCreated = db_context.Column(db_context.String(200))
    userUpdated = db_context.Column(db_context.String(200))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj