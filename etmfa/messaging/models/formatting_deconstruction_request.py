class FormattingDeconstructionRequest:
	""" POCO message request for an initial request for the formatting microservice"""

	QUEUE_NAME = 'formatting_deconstruction_request'

	def __init__(self, _id, fileName, filePath, sourceLang, targetLang):
		"""
		:param _id:  ID of the document translation request
		:fileName:  Name of the document to translate
		:filePath:  Fully-qualified path of the document to translate
		:sourceLang:  Short identifier for document source language
		:targetLang:  Short identifier for document target language
		"""
		self.id = _id
		self.fileName = fileName
		self.filePath = filePath
		self.sourceLang = sourceLang
		self.targetLang = targetLang
