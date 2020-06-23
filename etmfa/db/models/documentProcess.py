import datetime

from etmfa.db import db_context


class DocumentProcess(db_context.Model):
    __tablename__ = "etmfa_document_process"

    id = db_context.Column(db_context.String(50), primary_key=True)
    userId = db_context.Column(db_context.String(100))
    isProcessing = db_context.Column(db_context.Boolean())
    fileName = db_context.Column(db_context.String(300))
    documentFilePath = db_context.Column(db_context.String(500))
    percentComplete = db_context.Column(db_context.String(100))
    status = db_context.Column(db_context.String(100))
    feedback = db_context.Column(db_context.String(100))
    errorCode = db_context.Column(db_context.Integer())
    errorReason = db_context.Column(db_context.String(1000))
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj

    def from_post_request(request, _id, doc_path):

        this = DocumentProcess()
        this.id = _id
        this.isProcessing = True
        this.percentComplete = '0'

        if request['fileName'] is not None:
            this.fileName = safe_unicode(request['fileName'])
        else:
            file = request['file']
            this.fileName = safe_unicode(file.filename)

        return this


def safe_unicode(obj, *args):
    """ return the unicode representation of obj """
    try:
        return str(obj, *args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return str(ascii_text)
