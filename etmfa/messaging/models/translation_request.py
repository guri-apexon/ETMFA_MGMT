class TranslationRequest:
	""" POCO message request for an initial request from the translation microservice"""

	QUEUE_NAME = 'translation_request'

	def __init__(self, _id, source_lang, target_lang, xliff_path):
		"""
		:param _id:  ID of the document translation request
		:source_lang:  Source language short identifier
		:target_lang:  Target language short identifier
		:xliff_path:  Fully-qualified path of the document to translate
		"""
		self.id = _id
		self.source_lang = source_lang
		self.target_lang = target_lang
		self.xliff_path = xliff_path
