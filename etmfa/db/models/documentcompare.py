import datetime

from etmfa.db import db_context


class Documentcompare(db_context.Model):
    __tablename__ = "pd_document_compare"

    compareId = db_context.Column(db_context.String(300), primary_key=True)
    id1 = db_context.Column(db_context.String(300), primary_key=True)
    protocolNumber = db_context.Column(db_context.String(45))
    projectId = db_context.Column(db_context.String(45))
    versionNumber = db_context.Column(db_context.String(45))
    amendmentNumber = db_context.Column(db_context.String(45))
    documentStatus = db_context.Column(db_context.String(45))
    id2 = db_context.Column(db_context.String(300), primary_key=True)
    protocolNumber2 = db_context.Column(db_context.String(45))
    projectId2 = db_context.Column(db_context.String(45))
    versionNumber2 = db_context.Column(db_context.String(45))
    amendmentNumber2 = db_context.Column(db_context.String(45))
    documentStatus2 = db_context.Column(db_context.String(45))
    environment = db_context.Column(db_context.String(100))
    sourceSystem = db_context.Column(db_context.String(100))
    userId = db_context.Column(db_context.String(45))
    requestType = db_context.Column(db_context.String(45))
    iqvdata = db_context.Column(db_context.VARCHAR(None))
<<<<<<< HEAD
    base_IQV_xml_path = db_context.Column(db_context.String(500))
    compare_IQV_xml_path = db_context.Column(db_context.String(500))
    updated_IQV_xml_path = db_context.Column(db_context.String(500))
    similarity_score = db_context.Column(db_context.Integer())
=======
    baseIqvXmlPath = db_context.Column(db_context.String(500))
    compareIqvXmlPath = db_context.Column(db_context.String(500))
    updatedIqvXmlPath = db_context.Column(db_context.String(500))
    similarityScore = db_context.Column(db_context.Integer())
>>>>>>> c6d668b276b7ccbc897ec865ef956e1e6a0c5049

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
