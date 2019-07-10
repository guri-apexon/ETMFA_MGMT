import datetime

from ..db import db_context
from ..status import StatusEnum

class DocumentProcess(db_context.Model):
    __tablename__ = "eTMFA_document_process"

<<<<<<< HEAD
    #p_id = db_context.Column(db_context.Integer(), primary_key=True)
    id = db_context.Column(db_context.String(50), primary_key=True)
    is_processing = db_context.Column(db_context.Boolean())
    file_name = db_context.Column(db_context.String(100))

    # # Document paths
    document_file_path = db_context.Column(db_context.String(1000))

    error_code = db_context.Column(db_context.Integer())
    error_reason = db_context.Column(db_context.String(1000))
    time_created = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_updated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    Percent_complete = db_context.Column(db_context.String(100))
    #Percent_complete = db_context.Column(db_context.Enum(StatusEnumpercent), default=StatusEnum(0))
=======
    p_id = db_context.Column(db_context.Integer(), primary_key=True)
    id = db_context.Column(db_context.String(50))
    is_processing = db_context.Column(db_context.Boolean())
    #is_deleted = db_context.Column(db_context.Boolean(), default=False)
    file_name = db_context.Column(db_context.String(100))
    #source_lang_short = db_context.Column(db_context.String(10))
    #target_lang_short = db_context.Column(db_context.String(10))

    # # Document paths
    document_file_path = db_context.Column(db_context.String(500)) # Formatting Deconstruction
    #translated_xliff_path = db_context.Column(db_context.String(500)) # Translation Microservice
    #edited_xliff_path = db_context.Column(db_context.String(500)) # 3rd party edited
    #formatted_doc_path = db_context.Column(db_context.String(500)) # Formatting Reconstruction

    error_code = db_context.Column(db_context.Integer())
    error_reason = db_context.Column(db_context.String(500))
    time_created = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    last_updated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

>>>>>>> f358b797bf9629368279861b4828b78985d499f8
    status = db_context.Column(db_context.Enum(StatusEnum), default=StatusEnum(0))


    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
<<<<<<< HEAD
        obj['status'] = { 'Percent_complete': self.status.value, 'description': self.status.name}
=======
        obj['status'] = { 'id': self.status.value, 'description': self.status.name }
>>>>>>> f358b797bf9629368279861b4828b78985d499f8
        return obj

    def from_post_request(request, _id, doc_path):

        this = DocumentProcess()
        this.id = _id
        this.is_processing = True
<<<<<<< HEAD
        this.Percent_complete = '0'

        if request['file_name'] != None:
            this.file_name = request['file_name']
        else:
            file = request['file']
            this.file_name = file.filename
=======
        this.file_name = request['file_name']
        #this.source_lang_short = request['source_lang_short']
        #this.target_lang_short = request['target_lang_short']
>>>>>>> f358b797bf9629368279861b4828b78985d499f8

        return this