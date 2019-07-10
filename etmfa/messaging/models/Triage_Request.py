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

<<<<<<< HEAD
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
=======
		self.id       = str(_id)
		#self.fileName = filename
		self.filePath = filepath
		self.Customer = customer
		self.Protocol = protocol
		self.Country  = country
		self.Site     = site
		self.Document_Class = document_class
		self.TMF_IBR = tmf_ibr
		self.Blinded = blinded
		self.TMF_Environment     = tmf_environment
		self.Received_Date       = received_date
		self.site_personnel_list = site_personnel_list
		self.Priority = priority
>>>>>>> f358b797bf9629368279861b4828b78985d499f8

