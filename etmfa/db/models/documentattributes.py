import datetime

# from sqlalchemy import VARCHAR

from etmfa.db import db_context


class Documentattributes(db_context.Model):
    __tablename__ = "pd_document_attributes"


    id = db_context.Column(db_context.String(50), primary_key=True)
    user_id = db_context.Column(db_context.String(100))
    source_file_name = db_context.Column(db_context.String(300))
    document_file_path = db_context.Column(db_context.String(500))
    version_number = db_context.Column(db_context.String(300))
    protocol_number = db_context.Column(db_context.String(300))
    sponsor = db_context.Column(db_context.String(300))
    source_system = db_context.Column(db_context.String(300))
    document_status = db_context.Column(db_context.String(300))
    study_status = db_context.Column(db_context.String(300))
    amendment_number = db_context.Column(db_context.String(300))
    project_id = db_context.Column(db_context.String(100))
    environment = db_context.Column(db_context.String(300))
    indication = db_context.Column(db_context.String(300))
    molecule_device = db_context.Column(db_context.String(300))
    iqvdata_toc = db_context.Column(db_context.VARCHAR(None))
    iqvdata_soa = db_context.Column(db_context.VARCHAR(None))
    iqvdata_summary = db_context.Column(db_context.VARCHAR(None))
    iqvdata = db_context.Column(db_context.VARCHAR(None))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
