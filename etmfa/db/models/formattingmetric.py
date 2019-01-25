from ..db import db_context
from .metric import Metric

class FormattingMetric(db_context.Model):
	__tablename__ = "tms_formatting_metrics"

	id = db_context.Column(db_context.Integer(), primary_key=True)

	name = db_context.Column(db_context.String())
	value = db_context.Column(db_context.Integer())

	metric_id = db_context.Column(db_context.ForeignKey(Metric.id), nullable=False)
	metric = db_context.relationship(Metric, backref='formatting_metrics', lazy=False)

	def __init__(self, metric_id, name, value):
		self.metric_id = metric_id
		self.name = name
		self.value = value

	def __repr__(self):
		return '<Formatting Metric. Formatting Metric ID: {}>'.format(self.id)
	
	def as_dict(self):
		obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		obj[self.name] = self.value

		return obj