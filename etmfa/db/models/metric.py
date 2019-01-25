from ..db import db_context
from .documenttranslate import DocumentTranslate

class Metric(db_context.Model):
	__tablename__ = "tms_metrics"

	id = db_context.Column(db_context.Integer(), primary_key=True)
	document_translate_id = db_context.Column(db_context.ForeignKey(DocumentTranslate.p_id), nullable=False)	

	metric = db_context.relationship(DocumentTranslate, backref='metrics', lazy=False)

	def __init__(self, document_translate_id):
		self.document_translate_id = document_translate_id

	def __repr__(self):
		return '<Metric. Metrics ID: {}>'.format(self.id)
	
	def as_dict(self):
		obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		return obj