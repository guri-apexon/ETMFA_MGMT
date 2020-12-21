import datetime

from etmfa.db import db_context


class Documentcompare(db_context.Model):
    __tablename__ = "pd_document_compare"

    compare_id = db_context.Column(db_context.String(300), primary_key=True)
    doc_id = db_context.Column(db_context.String(300))
    protocol_number = db_context.Column(db_context.String(45))
    project_id = db_context.Column(db_context.String(45))
    version_number = db_context.Column(db_context.String(45))
    amendment_number = db_context.Column(db_context.String(45))
    document_status = db_context.Column(db_context.String(45))
    doc_id2 = db_context.Column(db_context.String(300))
    protocol_number2 = db_context.Column(db_context.String(45))
    project_id2 = db_context.Column(db_context.String(45))
    version_number2 = db_context.Column(db_context.String(45))
    amendment_number2 = db_context.Column(db_context.String(45))
    document_status2 = db_context.Column(db_context.String(45))
    environment = db_context.Column(db_context.String(100))
    source_system = db_context.Column(db_context.String(100))
    user_id = db_context.Column(db_context.String(45))
    request_type = db_context.Column(db_context.String(45))
    iqvdata = db_context.Column(db_context.VARCHAR(None))
    base_IQV_xml_path = db_context.Column(db_context.String(500))
    compare_IQV_xml_path = db_context.Column(db_context.String(500))
    updated_IQV_xml_path = db_context.Column(db_context.String(500))
    similarity_score = db_context.Column(db_context.Integer())

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
