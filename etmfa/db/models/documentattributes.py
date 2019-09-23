import datetime

from ..db import db_context

class Documentattributes(db_context.Model):
    __tablename__ = "etmfa_document_attributes"

    id                                    = db_context.Column(db_context.String(50), primary_key=True)
    fileName                              = db_context.Column(db_context.String(300))
    documentFilePath                      = db_context.Column(db_context.String(500))
    customer                              = db_context.Column(db_context.String(300))
    protocol                              = db_context.Column(db_context.String(300))
    country                               = db_context.Column(db_context.String(300))
    site                                  = db_context.Column(db_context.String(300))
    docClass                              = db_context.Column(db_context.String(300))
    priority                              = db_context.Column(db_context.String(300))
    receivedDate                          = db_context.Column(db_context.String(300))
    sitePersonnelList                     = db_context.Column(db_context.String(1000))
    tmfEnvironment                        = db_context.Column(db_context.String(300))
    tmfIbr                                = db_context.Column(db_context.String(300))
    unblinded                             = db_context.Column(db_context.Boolean())

    docCompConf                           = db_context.Column(db_context.String(100))
    docClassification                     = db_context.Column(db_context.String(500))
    docClassificationConf                 = db_context.Column(db_context.String(100))
    docDate                               = db_context.Column(db_context.String(500))
    docDateConf                           = db_context.Column(db_context.String(100))
    docDateType                           = db_context.Column(db_context.String(500))
    name                                  = db_context.Column(db_context.String(500))
    nameConf                              = db_context.Column(db_context.String(100))
    language                              = db_context.Column(db_context.String(500))
    languageConf                          = db_context.Column(db_context.String(100))
    subject                               = db_context.Column(db_context.String(500))
    subjectConf                           = db_context.Column(db_context.String(100))
    alcoacCheckError                      = db_context.Column(db_context.String(1000))
    alcoacCheckCompScore                  = db_context.Column(db_context.String(500))
    alcoacCheckCompScoreConf              = db_context.Column(db_context.String(100))
    docSubclassification                  = db_context.Column(db_context.String(500))
    docSubclassificationConf              = db_context.Column(db_context.String(100))
    documentRejected                      = db_context.Column(db_context.Boolean(), default = False)
    docClassificationElvis                = db_context.Column(db_context.String(500))
    attributeAuxillaryList                = db_context.Column(db_context.String(2000))
    timeCreated                           = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj
