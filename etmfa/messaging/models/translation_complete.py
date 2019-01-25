
import json

class TranslationComplete:
	""" POCO message response for an initial request from the translation microservice"""

	QUEUE_NAME = 'translation_complete'

	def from_msg(msg_str):
		"""
		:param _id:  ID of the document translation request
		:xliff_path:  Fully-qualified path of the xliff from translation deconstruction
		"""

		resp = json.loads(msg_str)

		this = {}
		this['id'] = resp['id']
		this['xliff_path'] = resp['xliff_path']
		this['metrics'] = resp['metrics']

		# metrics

		return this
