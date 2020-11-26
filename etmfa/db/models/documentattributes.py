import datetime

from etmfa.db import db_context


class Documentattributes(db_context.Model):
    __tablename__ = "pd_document_attributes"


    id = db_context.Column(db_context.String(50), primary_key=True)
    userId = db_context.Column(db_context.String(100))
    sourceFileName = db_context.Column(db_context.String(300))
    documentFilePath = db_context.Column(db_context.String(500))
    versionNumber = db_context.Column(db_context.String(300))
    protocolNumber = db_context.Column(db_context.String(300))
    sponsor = db_context.Column(db_context.String(300))
    sourceSystem = db_context.Column(db_context.String(300))
    documentStatus = db_context.Column(db_context.String(300))
    studyStatus = db_context.Column(db_context.String(300))
    amendmentNumber = db_context.Column(db_context.String(300))
    projectID = db_context.Column(db_context.String(100))
    environment = db_context.Column(db_context.String(300))
    indication = db_context.Column(db_context.String(300))
    moleculeDevice = db_context.Column(db_context.String(300))
    iqvData_TOC = db_context.Column(db_context.BLOB())
    iqvData_SOA = db_context.Column(db_context.BLOB())
    iqvData_Summary = db_context.Column(db_context.BLOB())


    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
