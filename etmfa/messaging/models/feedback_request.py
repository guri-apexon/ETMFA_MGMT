class feedbackrequest:
	""" POCO message request for an initial request for the formatting microservice"""

	QUEUE_NAME = 'feedback_request'

	def __init__(self, _id, document_file_path,feedback_source, customer, protocol, country,  site,
				 			 document_class, document_date, document_classification,
				             name, language, document_rejected, attribute_auxillary_list
				 ):
		"""
		:param _id:  ID of the document translation request
		:fileName:  Name of the document to translate
		:filePath:  Fully-qualified path of the document to translate
		:sourceLang:  Short identifier for document source language
		:targetLang:  Short identifier for document target language
		"""
		self.id                       = str(_id)
		self.document_file_path       = document_file_path
		self.feedback_source          = feedback_source
		self.customer                 = customer
		self.protocol                 = protocol
		self.country                  = country
		self.site                     = site
		self.document_class           = document_class
		self.document_date            = document_date
		self.document_classification  = document_classification
		self.name                     = name
		self.language                 = language
		self.document_rejected        = document_rejected
		self.attribute_auxillary_list = attribute_auxillary_list

