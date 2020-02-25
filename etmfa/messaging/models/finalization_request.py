class finalizationRequest:
    QUEUE_NAME = 'finalization_request'

    def __init__(self, _id, IQVXMLPath):
        self.id = _id
        self.IQVXMLPath = IQVXMLPath
