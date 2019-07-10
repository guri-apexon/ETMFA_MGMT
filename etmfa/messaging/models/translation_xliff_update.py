# class TranslationXliffUpdate:
# 	""" POCO message request signalling a user update to the XLIFF file"""
#
# 	QUEUE_NAME = 'translation_xliff_update'
#
# 	def __init__(self, _id, xliff_path):
# 		"""
# 		:param _id:  ID of the document translation request.
# 		:xliff_path:  Fully-qualified path of the xliff that was updated.
# 		"""
# 		self.id = _id
# 		self.xliff_path = xliff_path
