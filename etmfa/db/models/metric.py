from ..db import db_context
import datetime

class Metric(db_context.Model):
	__tablename__ = "etmfa_document_metrics"

	id                              = db_context.Column(db_context.String(50), primary_key=True)
	totalProcessTime                = db_context.Column(db_context.String(200))
	queueWaitTime                   = db_context.Column(db_context.String(200))
	triageMachineName               = db_context.Column(db_context.String(200))
	triageVersion                   = db_context.Column(db_context.String(200))
	triageStartTime                 = db_context.Column(db_context.String(200))
	triageEndTime                   = db_context.Column(db_context.String(200))
	triageProcTime                  = db_context.Column(db_context.String(200))
	digitizerMachineName            = db_context.Column(db_context.String(200))
	digitizerVersion                = db_context.Column(db_context.String(200))
	digitizerStartTime              = db_context.Column(db_context.String(200))
	digitizerEndTime                = db_context.Column(db_context.String(200))
	digitizerProcTime               = db_context.Column(db_context.String(200))
	classificationMachineName       = db_context.Column(db_context.String(200))
	classificationVersion           = db_context.Column(db_context.String(200))
	classificationStartTime         = db_context.Column(db_context.String(200))
	classificationEndTime           = db_context.Column(db_context.String(200))
	classificationProcTime          = db_context.Column(db_context.String(200))
	attExtractionMachineName        = db_context.Column(db_context.String(200))
	attExtractionVersion            = db_context.Column(db_context.String(200))
	attExtractionStartTime          = db_context.Column(db_context.String(200))
	attExtractionEndTime            = db_context.Column(db_context.String(200))
	attExtractionProcTime           = db_context.Column(db_context.String(200))
	finalizationMachineName         = db_context.Column(db_context.String(200))
	finalizationVersion             = db_context.Column(db_context.String(200))
	finalizationStartTime           = db_context.Column(db_context.String(200))
	finalizationEndTime             = db_context.Column(db_context.String(200))
	finalizationProcTime            = db_context.Column(db_context.String(200))
	docType                         = db_context.Column(db_context.String(200))
	docTypeOriginal                 = db_context.Column(db_context.String(200))
	docSegments                     = db_context.Column(db_context.String(200))
	docPages                        = db_context.Column(db_context.String(200))
	timeCreated                     = db_context.Column(db_context.DateTime(timezone=True), default=datetime.datetime.utcnow)

	def __init__(self, id):
		self.id = id

	def __repr__(self):
		return '<Metric. Metrics ID: {}>'.format(self.id)
	
	def as_dict(self):
		obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		return obj