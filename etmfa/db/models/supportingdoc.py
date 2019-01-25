from ..db import db_context
from .documenttranslate import DocumentTranslate

class SupportingDoc(db_context.Model):
	__tablename__ = "tms_supporting_docs"

	id = db_context.Column(db_context.Integer(), primary_key=True)
	description = db_context.Column(db_context.String())
	file_path = db_context.Column(db_context.String())

	document_translate_id = db_context.Column(db_context.ForeignKey(DocumentTranslate.p_id), nullable=False)	

	supporting_docs = db_context.relationship(DocumentTranslate, backref='supporting_docs', lazy=False)

	def __init__(self, document_translate_id, file_path, desc):
		self.document_translate_id = document_translate_id
		self.file_path = file_path
		self.description = desc

	def __repr__(self):
		return '<Supporting Doc. Supporting Docs ID: {}>'.format(self.id)
	
	def as_dict(self):
		obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		return obj