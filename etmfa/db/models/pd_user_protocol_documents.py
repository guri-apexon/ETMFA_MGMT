import datetime

from etmfa.db import db_context


class pd_user_protocol_documents(db_context.Model):
    __tablename__ = "pd_user_protocol_documents"

    id = db_context.Column(db_context.String(100), primary_key=True)
    userid = db_context.Column(db_context.String(100), primary_key=True)
    filename = db_context.Column(db_context.String(100))
    filepath = db_context.Column(db_context.String(500))
    protocol = db_context.Column(db_context.String(500))
    protocolname = db_context.Column(db_context.String(500))
    projectid = db_context.Column(db_context.Integer())
    sponser = db_context.Column(db_context.String(200))
    indication = db_context.Column(db_context.String(500))
    molecule = db_context.Column(db_context.String(500))
    amendment = db_context.Column(db_context.String(500))
    versionnumber = db_context.Column(db_context.Float())
    documentstatus = db_context.Column(db_context.String(100))
    draftversion = db_context.Column(db_context.Float())
    errorcode = db_context.Column(db_context.Integer())
    errorreason = db_context.Column(db_context.String(500))
    status = db_context.Column(db_context.String(100))
    phase = db_context.Column(db_context.String(500))
    digitizedconfidenceinterval = db_context.Column(db_context.String(500))
    completenessofdigitization = db_context.Column(db_context.String(100))
    protocoltitle = db_context.Column(db_context.String(500))
    studystatus = db_context.Column(db_context.String(500))
    sourcesystem = db_context.Column(db_context.String(500))
    environment = db_context.Column(db_context.String(200))
    uploaddate = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    timecreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    timeupdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    usercreated = db_context.Column(db_context.String(200))
    usermodified = db_context.Column(db_context.String(200))
    approvaldate = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    isactive = db_context.Column(db_context.Boolean(), default=False)
    iqvxmlpath = db_context.Column(db_context.String(500))
    nctid = db_context.Column(db_context.String(100))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
