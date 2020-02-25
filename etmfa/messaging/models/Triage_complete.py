import json


class TriageComplete:
    QUEUE_NAME = 'Triage_Complete'

    def from_msg(msg_str):
        resp = json.loads(msg_str)

        this = {}
        this['id'] = resp['id']
        this['IQVXMLPath'] = resp['IQVXMLPath']

        return this
