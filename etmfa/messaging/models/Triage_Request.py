class TriageRequest:
	""" POCO message request for an initial request for the formatting microservice"""

	QUEUE_NAME = 'Triage_Request'

	def __init__(self, _id, filename, filepath, customer, protocol, country, site, document_class, tmf_ibr,
				 blinded, tmf_environment, received_date, site_personnel_list, priority):
		"""
		:param _id:  ID of the document translation request
		:fileName:  Name of the document to translate
		:filePath:  Fully-qualified path of the document to translate
		:sourceLang:  Short identifier for document source language
		:targetLang:  Short identifier for document target language
		"""

		self.id = str(_id)
		self.filename = filename
		self.filepath = filepath
		self.customer = customer
		self.protocol = protocol
		self.country = country
		self.site = site
		self.document_class = document_class
		self.tmf_ibr = tmf_ibr
		self.blinded = blinded
		self.tmf_environment = tmf_environment
		self.received_date = received_date
		self.site_personnel_list = site_personnel_list
		self.priority = priority

