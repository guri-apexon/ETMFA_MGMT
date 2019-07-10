<<<<<<< HEAD
from ..db import db_context
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Sequence
from ..status import StatusEnum
import datetime

=======
import datetime

from ..db import db_context
from ..status import StatusEnum
>>>>>>> f358b797bf9629368279861b4828b78985d499f8

class Documentfeedback(db_context.Model):
    __tablename__ = "eTMFA_document_feedback"

<<<<<<< HEAD

    p_id = db_context.Column(db_context.String(50), primary_key=True)
=======
    p_id = db_context.Column(db_context.Integer(), primary_key=True)
>>>>>>> f358b797bf9629368279861b4828b78985d499f8
    id = db_context.Column(db_context.String(50))
    feedback_source = db_context.Column(db_context.String(100))
    customer        = db_context.Column(db_context.String(300))
    protocol        = db_context.Column(db_context.String(300))
    country         = db_context.Column(db_context.String(300))
    site            = db_context.Column(db_context.String(300))
    document_class  = db_context.Column(db_context.String(300))
    document_date   = db_context.Column(db_context.String(50))
    document_classification = db_context.Column(db_context.String(100))
    name            = db_context.Column(db_context.String(300))
    language        = db_context.Column(db_context.String(3))
    document_rejected = db_context.Column(db_context.String(1))
<<<<<<< HEAD
    attribute_auxillary_list = db_context.Column(db_context.String(2000))

    #time_created = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_updated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
=======
    #attribute_auxillary_list = db_context.Column(db_context.String(2000))

    # #is_deleted = db_context.Column(db_context.Boolean(), default=False)
    # file_name = db_context.Column(db_context.String(100))
    # #source_lang_short = db_context.Column(db_context.String(10))
    # #target_lang_short = db_context.Column(db_context.String(10))
    #
    # # # Document paths
    # document_file_path = db_context.Column(db_context.String(500)) # Formatting Deconstruction
    # #translated_xliff_path = db_context.Column(db_context.String(500)) # Translation Microservice
    # #edited_xliff_path = db_context.Column(db_context.String(500)) # 3rd party edited
    # #formatted_doc_path = db_context.Column(db_context.String(500)) # Formatting Reconstruction
    #
    # error_code = db_context.Column(db_context.Integer())
    # error_reason = db_context.Column(db_context.String(500))
    # time_created = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    # last_updated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    #
    # status = db_context.Column(db_context.Enum(StatusEnum), default=StatusEnum(0))
>>>>>>> f358b797bf9629368279861b4828b78985d499f8


    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
<<<<<<< HEAD
        return obj

=======
        #obj['status'] = { 'id': self.status.value, 'description': self.status.name }
        return obj

    # def from_post_request(request, _id, doc_path):
    #
    #     this = DocumentProcess()
    #     this.id = _id
    #     this.is_processing = True
    #     this.file_name = request['file_name']
    #     #this.source_lang_short = request['source_lang_short']
    #     #this.target_lang_short = request['target_lang_short']
    #
    #     return this
>>>>>>> f358b797bf9629368279861b4828b78985d499f8
