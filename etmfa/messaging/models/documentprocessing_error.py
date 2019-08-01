import json, logging

class documentprocessingerror:
	""" Message response from the formatting service indicating an error"""

	QUEUE_NAME = 'documentprocessing_error'

	def from_msg(msg_str):
		"""
		Args:
		    msg_str (str): The string JSON message from the central message broker.

		Returns:
		    dictionary: with message properties
		"""
		resp = json.loads(msg_str)

		this = {}
		this['id']           = resp['id']
		this['service_name'] = resp['service_name']
		this['error_code']   = resp['error_code']
		this['error_reason'] = resp['error_message']

		return this