import datetime

from ..db import db_context
from ..status import StatusEnum

class Documentattributes(db_context.Model):
    __tablename__ = "eTMFA_document_attributes"

<<<<<<< HEAD
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
=======
    p_id = db_context.Column(db_context.Integer(), primary_key=True)
    id = db_context.Column(db_context.String(50))
    document_composite_confidence = db_context.Column(db_context.String(3))
    customer = db_context.Column(db_context.String(200))
    protocol = db_context.Column(db_context.String(200))
    country  = db_context.Column(db_context.String(200))
    site     = db_context.Column(db_context.String(200))
    document_class = db_context.Column(db_context.String(200))
    document_date  = db_context.Column(db_context.String(10))
    document_date_confidence = db_context.Column(db_context.String(3))
    document_date_type       = db_context.Column(db_context.String(100))
    document_classification  = db_context.Column(db_context.String(100))
    document_classification_confidence  =  db_context.Column(db_context.String(3))
    name  = db_context.Column(db_context.String(300))
    name_confidence  = db_context.Column(db_context.String(3))
    document_subclassification  = db_context.Column(db_context.String(100))
    document_subclassification_confidence  = db_context.Column(db_context.String(3))
    subject  = db_context.Column(db_context.String(50))
    subject_confidence  = db_context.Column(db_context.String(3))
    language  = db_context.Column(db_context.String(50))
    language_confidence  = db_context.Column(db_context.String(3))
    alcoac_check_composite_score = db_context.Column(db_context.String(100))
    alcoac_check_composite_score_confidence = db_context.Column(db_context.String(3))
    alcoal_check_error  = db_context.Column(db_context.String(500))
    blinded  =  db_context.Column(db_context.Boolean())
    datetimecreated  = db_context.Column(db_context.String(100))
    document_rejected = db_context.Column(db_context.String(500))
    priority  = db_context.Column(db_context.String(10))
    received_date  = db_context.Column(db_context.String(50))
    site_personnel_list  = db_context.Column(db_context.String(300))
    tmf_environment = db_context.Column(db_context.String(50))
    tmf_ibr  = db_context.Column(db_context.String(10))

    # 'attribute_auxillary_list': fields.List(fields.Nested(kv_pair_model)),
    #
    #
    # is_processing = db_context.Column(db_context.Boolean())
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
        #obj['status'] = { 'id': self.status.value, 'description': self.status.name }
        return obj
<<<<<<< HEAD
=======

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
