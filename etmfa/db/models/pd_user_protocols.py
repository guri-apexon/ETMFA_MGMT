import datetime

from etmfa.db import db_context


class PDUserProtocols(db_context.Model):
    __tablename__ = "pd_user_protocols"

    isActive = db_context.Column(db_context.Boolean(), default=True)
    id = db_context.Column(db_context.Integer(), primary_key=True,autoincrement=True)
    userId = db_context.Column(db_context.String(200), primary_key=True)
    protocol = db_context.Column(db_context.String(200))
    projectId = db_context.Column(db_context.String(200))
    follow = db_context.Column(db_context.Boolean(), default=False)
    userRole = db_context.Column(db_context.String(200), default="primary")
    
    userCreated = db_context.Column(db_context.String(100))
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    userUpdated = db_context.Column(db_context.String(100))
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
