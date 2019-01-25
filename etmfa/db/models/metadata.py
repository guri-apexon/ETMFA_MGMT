from ..db import db_context
from .documenttranslate import DocumentTranslate

class IQMetadata(db_context.Model):
	__tablename__ = "tms_metadata"

	id = db_context.Column(db_context.Integer(), primary_key=True)
	document_translate_id = db_context.Column(db_context.ForeignKey(DocumentTranslate.p_id), nullable=False)
	iq_metadata = db_context.relationship(DocumentTranslate, backref='iq_metadata', lazy=False)

	name = db_context.Column(db_context.String())
	value = db_context.Column(db_context.String())


	def __init__(self, document_translate_id, name, value):
		self.document_translate_id = document_translate_id
		self.name = name
		self.value = value

	def __repr__(self):
		return '<IQ Metadata. IQ Metadata ID: {}>'.format(self.id)
	
	def as_dict(self):
		obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		return obj