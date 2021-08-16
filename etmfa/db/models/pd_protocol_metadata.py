import datetime

from etmfa.db import db_context


class PDProtocolMetadata(db_context.Model):
    __tablename__ = "pd_protocol_metadata"

    # intake fields
    isActive = db_context.Column(db_context.Boolean(), default=True)
    id = db_context.Column(db_context.String(100), primary_key=True)
    userId = db_context.Column(db_context.String(100), primary_key=True)
    fileName = db_context.Column(db_context.String(100))
    documentFilePath = db_context.Column(db_context.String(500))
    protocol = db_context.Column(db_context.String(500))
    projectId = db_context.Column(db_context.String(500))
    sponsor = db_context.Column(db_context.String(200))
    indication = db_context.Column(db_context.String(500))
    moleculeDevice = db_context.Column(db_context.String(500))
    amendment = db_context.Column(db_context.String(500))
    versionNumber = db_context.Column(db_context.String(200))
    documentStatus = db_context.Column(db_context.String(100))
    draftVersion = db_context.Column(db_context.String(500))
    uploadDate = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    
    # processing fields
    isProcessing= db_context.Column(db_context.Boolean(), default=True)
    errorCode = db_context.Column(db_context.Integer())
    errorReason = db_context.Column(db_context.String(500))
    percentComplete = db_context.Column(db_context.String(100))
    status = db_context.Column(db_context.String(100))
    qcStatus = db_context.Column(db_context.String(100))
    compareStatus = db_context.Column(db_context.String(100))
    iqvXmlPathProc = db_context.Column(db_context.String(1500))
    iqvXmlPathComp = db_context.Column(db_context.String(1500))
    
    # output fields
    protocolTitle = db_context.Column(db_context.VARCHAR(None))
    shortTitle = db_context.Column(db_context.String(1500))
    phase = db_context.Column(db_context.String(500))
    digitizedConfidenceInterval = db_context.Column(db_context.String(500))
    completenessOfDigitization = db_context.Column(db_context.String(100))
    approvalDate = db_context.Column(db_context.DateTime(timezone=True))

    # placeholders
    studyStatus = db_context.Column(db_context.String(500))
    sourceSystem = db_context.Column(db_context.String(500))
    environment = db_context.Column(db_context.String(200))
    nctId = db_context.Column(db_context.String(100))

    # Audit fields
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    lastUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    userCreated = db_context.Column(db_context.String(200))
    userUpdated = db_context.Column(db_context.String(200))


    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
    
    def from_post_request(request, _id, doc_path):
    
        this = PDProtocolMetadata()
        this.id = _id
        this.isProcessing = True
        this.percentComplete = '0'

        if request['sourceFileName'] is not None:
            this.sourceFileName = safe_unicode(request['sourceFileName'])
        else:
            file = request['file']
            this.sourceFileName = safe_unicode(file.filename)

        return this


def safe_unicode(obj, *args):
    """ return the unicode representation of obj """
    try:
        return str(obj, *args)
    except UnicodeDecodeError:
        # obj is byte string
        ascii_text = str(obj).encode('string_escape')
        return str(ascii_text)
