import datetime
from etmfa.db import db_context

class Protocolalert(db_context.Model):
    __tablename__ = "pd_protocol_alert"

    id = db_context.Column(db_context.String(100), primary_key=True)
    aidocId = db_context.Column(db_context.String(100), primary_key=True)
    protocol = db_context.Column(db_context.String(500))
    protocolTitle = db_context.Column(db_context.String(1500))
    readFlag = db_context.Column(db_context.Boolean(), default=False)
    readTime = db_context.Column(db_context.DateTime(timezone=True))
    emailSentFlag = db_context.Column(db_context.Boolean(), default=False)
    emailSentTime = db_context.Column(db_context.DateTime(timezone=True))
    alertGeneratedTime = db_context.Column(db_context.DateTime(timezone=True))
    approvalDate = db_context.Column(db_context.Date())
    isActive = db_context.Column(db_context.Boolean(), default=True)
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    timeUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)



    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj