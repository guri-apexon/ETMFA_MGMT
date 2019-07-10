from ..db import db_context
from .documentProcess import DocumentProcess

class Metric(db_context.Model):
	__tablename__ = "eTMFA_metrics"

	id = db_context.Column(db_context.String(50), primary_key=True)
	#document_processing_id          = db_context.Column(db_context.ForeignKey(DocumentProcess.id), nullable=False)
	triage_start_time               = db_context.Column(db_context.String(200))
	triage_end_time                 = db_context.Column(db_context.String(200))
	triage_proc_time             = db_context.Column(db_context.String(200))
	digitizer_start_time            = db_context.Column(db_context.String(200))
	digitizer_end_time              = db_context.Column(db_context.String(200))
	digitizer_proc_time          = db_context.Column(db_context.String(200))
	classification_start_time       = db_context.Column(db_context.String(200))
	classification_end_time         = db_context.Column(db_context.String(200))
	classification_proc_time     = db_context.Column(db_context.String(200))
	attributeextraction_start_time  = db_context.Column(db_context.String(200))
	attributeextraction_end_time    = db_context.Column(db_context.String(200))
	attributeextraction_proc_time= db_context.Column(db_context.String(200))
	finalization_start_time         = db_context.Column(db_context.String(200))
	finalization_end_time           = db_context.Column(db_context.String(200))
	finalization_process_time       = db_context.Column(db_context.String(200))

	#metric = db_context.relationship(DocumentProcess, backref='metrics', lazy=False)

	def __init__(self, document_processing_id):
		self.document_processing_id = document_processing_id

	def __repr__(self):
		return '<Metric. Metrics ID: {}>'.format(self.id)
	
	def as_dict(self):
		obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		return obj