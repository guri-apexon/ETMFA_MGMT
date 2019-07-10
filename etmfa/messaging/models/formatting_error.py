# import json, logging
#
# class FormattingError:
# 	""" Message response from the formatting service indicating an error"""
#
# 	QUEUE_NAME = 'formatting_error'
#
# 	def from_msg(msg_str):
# 		"""
# 		Args:
# 		    msg_str (str): The string JSON message from the central message broker.
#
# 		Returns:
# 		    dictionary: with message properties
# 		"""
# 		resp = json.loads(msg_str)
#
# 		this = {}
# 		this['id'] = resp['id']
# 		this['logId'] = resp['logId']
# 		this['message'] = resp['message']
# 		this['stackTrace'] = resp['stackTrace']
#
# 		return this