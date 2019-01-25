class FormattingReconstructionRequest:
	"""
	POCO message request for a reconstruction request for the formatting microservice after a human-translated XLIFF has been received.
	"""

	QUEUE_NAME = 'formatting_reconstruction_request'

	def __init__(self, _id, filePath):
		"""
		:param _id:  ID of the document translation request
		:param filePath:  Fully-qualified path of the XLIFF file for reconstruction
		"""
		self.id = _id
		self.filePath = filePath
