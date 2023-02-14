import datetime
from etmfa.db import db_context

class amp_server_run_info(db_context.Model):
    __tablename__ = "amp_server_run_info"

    id = db_context.Column(db_context.Integer(), primary_key=True)
    run_id = db_context.Column(db_context.Integer())
    aidoc_id = db_context.Column(db_context.String(256))
    omop_xml_path = db_context.Column(db_context.String(256))
    updated_omop_xml_path = db_context.Column(db_context.String(256))
    run_url = db_context.Column(db_context.String(256))
    run_status = db_context.Column(db_context.String(32))
    created_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    is_deleted = db_context.Column(db_context.Boolean(), default=False)
    deleted_on = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    process_time = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
