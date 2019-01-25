import datetime

from ..db import db_context
from ..status import StatusEnum

class DocumentTranslate(db_context.Model):
    __tablename__ = "tms_document_translate" 

    p_id = db_context.Column(db_context.Integer(), primary_key=True)
    id = db_context.Column(db_context.String())
    is_processing = db_context.Column(db_context.Boolean())
    is_deleted = db_context.Column(db_context.Boolean(), default=False)
    file_name = db_context.Column(db_context.String())
    source_lang_short = db_context.Column(db_context.String())
    target_lang_short = db_context.Column(db_context.String())

    # Document paths
    deconstructed_xliff_path = db_context.Column(db_context.String()) # Formatting Deconstruction
    translated_xliff_path = db_context.Column(db_context.String()) # Translation Microservice
    edited_xliff_path = db_context.Column(db_context.String()) # 3rd party edited
    formatted_doc_path = db_context.Column(db_context.String()) # Formatting Reconstruction

    error_code = db_context.Column(db_context.Integer())
    error_reason = db_context.Column(db_context.String())
    time_created = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_updated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    status = db_context.Column(db_context.Enum(StatusEnum), default=StatusEnum(0))

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        obj['status'] = { 'id': self.status.value, 'description': self.status.name }
        return obj

    def from_post_request(request, _id, doc_path):

        this = DocumentTranslate()
        this.id = _id
        this.is_processing = True
        this.file_name = request['file_name']
        this.source_lang_short = request['source_lang_short']
        this.target_lang_short = request['target_lang_short']

        return this