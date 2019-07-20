import datetime

from ..db import db_context
from ..status import StatusEnum

class Documentattributes(db_context.Model):
    __tablename__ = "eTMFA_document_attributes"

    #p_id                                  = db_context.Column(db_context.Integer(), primary_key=True)
    id                                    = db_context.Column(db_context.String(50), primary_key=True)
    doc_comp_conf                         = db_context.Column(db_context.String(30))
    customer                              = db_context.Column(db_context.String(200))
    protocol                              = db_context.Column(db_context.String(200))
    country                               = db_context.Column(db_context.String(200))
    site                                  = db_context.Column(db_context.String(200))
    doc_class                             = db_context.Column(db_context.String(500))
    doc_date                              = db_context.Column(db_context.String(500))
    doc_date_conf                         = db_context.Column(db_context.String(30))
    doc_date_type                         = db_context.Column(db_context.String(100))
    doc_classification                    = db_context.Column(db_context.String(500))
    doc_classification_conf               = db_context.Column(db_context.String(30))
    name                                  = db_context.Column(db_context.String(300))
    name_conf                             = db_context.Column(db_context.String(30))
    doc_subclassification                 = db_context.Column(db_context.String(500))
    doc_subclassification_conf            = db_context.Column(db_context.String(30))
    subject                               = db_context.Column(db_context.String(500))
    subject_conf                          = db_context.Column(db_context.String(30))
    language                              = db_context.Column(db_context.String(500))
    language_conf                         = db_context.Column(db_context.String(30))
    alcoac_check_comp_score               = db_context.Column(db_context.String(100))
    alcoac_check_comp_score_conf          = db_context.Column(db_context.String(30))
    alcoal_check_error                    = db_context.Column(db_context.String(1000))
    blinded                               =  db_context.Column(db_context.Boolean())
    datetimecreated                       = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)
    doc_rejected                          = db_context.Column(db_context.String(500))
    priority                              = db_context.Column(db_context.String(100))
    received_date                         = db_context.Column(db_context.String(100))
    site_personnel_list                   = db_context.Column(db_context.String(1000))
    tmf_environment                       = db_context.Column(db_context.String(100))
    tmf_ibr                               = db_context.Column(db_context.String(100))

    # 'attribute_auxillary_list': fields.List(fields.Nested(kv_pair_model)),

    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        #obj['status'] = { 'id': self.status.value, 'description': self.status.name }
        return obj
