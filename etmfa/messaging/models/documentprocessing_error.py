import json, logging

class documentprocessingerror:

	QUEUE_NAME = 'documentprocessing_error'

	def from_msg(msg_str):

		resp = json.loads(msg_str)

		this = {}
		this['id']           = resp['id']
		this['service_name'] = resp['service_name']
		this['error_code']   = resp['error_code']
		this['error_reason'] = resp['error_message']

		return this