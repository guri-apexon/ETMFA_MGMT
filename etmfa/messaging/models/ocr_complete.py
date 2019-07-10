
import json, logging

class ocrcomplete:
	""" POCO message response for an initial request from the formatting microservice"""

	QUEUE_NAME = 'ocr_complete'

	def from_msg(msg_str):
		"""
		:param _id:  ID of the document translation request
		:fileName:  Name of the document to translate
		:xliffPath:  Fully-qualified path of the xliff from formatting deconstruction
		"""
		resp = json.loads(msg_str)

		this = {}
		this['id'] = resp['id']
		this['fileName'] = resp['fileName']
		this['IQVXMLPath'] = resp['IQVXMLPath']

		return this