
import json, logging

class finalizationComplete:

	QUEUE_NAME = 'finalization_complete'

	def from_msg(msg_str):

		resp = json.loads(msg_str)

		this = {}
		this['id'] = resp['id']
		this['fileName'] = resp['fileName']
		this['IQVXMLPath'] = resp['IQVXMLPath']

		return this