
import json, logging

class feedbackComplete:

	QUEUE_NAME = 'feedback_complete'

	def from_msg(msg_str):

		resp = json.loads(msg_str)

		this = {}
		this['id'] = resp['id']
		this['fileName'] = resp['fileName']

		return this