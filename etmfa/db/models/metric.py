from ..db import db_context

class Metric(db_context.Model):
	__tablename__ = "etmfa_document_metrics"

	id                              = db_context.Column(db_context.String(50), primary_key=True)
	total_process_time              = db_context.Column(db_context.String(200))
	queue_wait_time                 = db_context.Column(db_context.String(200))
	triage_machine_name             = db_context.Column(db_context.String(200))
	triage_version                  = db_context.Column(db_context.String(200))
	triage_start_time               = db_context.Column(db_context.String(200))
	triage_end_time                 = db_context.Column(db_context.String(200))
	triage_proc_time                = db_context.Column(db_context.String(200))
	digitizer_machine_name          = db_context.Column(db_context.String(200))
	digitizer_version               = db_context.Column(db_context.String(200))
	digitizer_start_time            = db_context.Column(db_context.String(200))
	digitizer_end_time              = db_context.Column(db_context.String(200))
	digitizer_proc_time             = db_context.Column(db_context.String(200))
	classification_machine_name     = db_context.Column(db_context.String(200))
	classification_version          = db_context.Column(db_context.String(200))
	classification_start_time       = db_context.Column(db_context.String(200))
	classification_end_time         = db_context.Column(db_context.String(200))
	classification_proc_time        = db_context.Column(db_context.String(200))
	att_extraction_machine_name     = db_context.Column(db_context.String(200))
	att_extraction_version          = db_context.Column(db_context.String(200))
	att_extraction_start_time       = db_context.Column(db_context.String(200))
	att_extraction_end_time         = db_context.Column(db_context.String(200))
	att_extraction_proc_time        = db_context.Column(db_context.String(200))
	finalization_machine_name       = db_context.Column(db_context.String(200))
	finalization_version            = db_context.Column(db_context.String(200))
	finalization_start_time         = db_context.Column(db_context.String(200))
	finalization_end_time           = db_context.Column(db_context.String(200))
	finalization_proc_time          = db_context.Column(db_context.String(200))
	doc_type                        = db_context.Column(db_context.String(200))
	doc_type_original               = db_context.Column(db_context.String(200))
	doc_segments                    = db_context.Column(db_context.String(200))
	doc_pages                       = db_context.Column(db_context.String(200))

	def __init__(self, id):
		self.id = id

	def __repr__(self):
		return '<Metric. Metrics ID: {}>'.format(self.id)
	
	def as_dict(self):
		obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		return obj