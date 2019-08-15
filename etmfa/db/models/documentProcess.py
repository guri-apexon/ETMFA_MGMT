import datetime

from ..db import db_context

class DocumentProcess(db_context.Model):
    __tablename__ = "etmfa_document_process"

    id                 = db_context.Column(db_context.String(50), primary_key=True)
    is_processing      = db_context.Column(db_context.Boolean())
    file_name          = db_context.Column(db_context.String(300))
    document_file_path = db_context.Column(db_context.String(500))
    error_code         = db_context.Column(db_context.Integer())
    error_reason       = db_context.Column(db_context.String(1000))
    time_created       = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_updated       = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    Percent_complete   = db_context.Column(db_context.String(100))
    status             = db_context.Column(db_context.String(100))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj

    def from_post_request(request, _id, doc_path):

        this = DocumentProcess()
        this.id = _id
        this.is_processing = True
        this.Percent_complete = '0'

        if request['file_name'] is not None:
            this.file_name = request['file_name']
        else:
            file = request['file']
            this.file_name = file.filename

        return this