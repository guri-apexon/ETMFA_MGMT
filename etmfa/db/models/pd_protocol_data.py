import datetime

from etmfa.db import db_context


class Protocoldata(db_context.Model):
    __tablename__ = "pd_protocol_data"


    id = db_context.Column(db_context.String(50), primary_key=True)
    userId = db_context.Column(db_context.String(100), primary_key=True)
    fileName = db_context.Column(db_context.String(300))
    documentFilePath = db_context.Column(db_context.String(500))
    iqvdataToc = db_context.Column(db_context.NVARCHAR(None))
    iqvdataSoa = db_context.Column(db_context.NVARCHAR(None))
    iqvdataSoaStd = db_context.Column(db_context.NVARCHAR(None))
    iqvdataSummary = db_context.Column(db_context.NVARCHAR(None))
    iqvdata = db_context.Column(db_context.NVARCHAR(None))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj

