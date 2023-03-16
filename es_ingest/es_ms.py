
from mq_service import MicroServiceWrapper,ExecutionContext,Config
from multiprocessing import Process
import requests
from http import HTTPStatus
import json

class EsGenericException(Exception):
    def __init__(self,msg,_id=None):
        self.id = _id
        self.msg=msg

    def __str__(self):
        return f'(es_ingestion failure :  {self.msg} for id {self.id})'


class ElasticIngestion(ExecutionContext):
    def __init__(self,config):
        self.config=config
        self.url=config.PD_UI_BACKEND_LINK
        auth_details=config.AUTH_PD_UI_BACKEND
        self.user_name=auth_details['user_name']
        self.password=auth_details['password']
        ExecutionContext.__init__(self,config.CONTEXT_MAX_ACTIVE_TIME)
        self.token_headers=self._get_tokens()

    def _get_tokens(self):
        token_header = {}
        header_str = {'Content-Type': 'application/x-www-form-urlencoded'}
        data_str = f'grant_type=&username={self.user_name}&password={self.password}'
        url=self.url+"/token/form_data"
        response_token = requests.post(url, headers = header_str, data=data_str)
        if response_token.status_code == HTTPStatus.OK:
            response_token_dict = json.loads(response_token.text)
            token_header = {'Authorization': f'Bearer {response_token_dict.get("access_token")}'}
            return token_header
        else:
            raise EsGenericException("Unable to get token  headers")
        
    def on_init(self):
        """
        intialization if any needed
        """

        pass

    def on_callback(self, data):
        """
        return: original response or what should be sent next.
        """
        msg=list(data.values())[0]
        key = 'docId' if 'docId' in msg else 'doc_id'
        doc_id=msg[key]
        response=requests.post(self.url+"/elastic_ingest/",
                    params={"aidoc_id": doc_id},
                    headers=self.token_headers)
        if response.status_code == HTTPStatus.OK:
            res_json = response.json()
            if res_json['success'] == False:
                raise EsGenericException(" Failed to get doc id ",doc_id)
        else:
            raise EsGenericException(" Failed to get doc id ",doc_id)
        return data

    def on_release(self):
        """
        resource if any needs to be released
        """
        pass

class ElasticIngestionRunner(Process):
    def __init__(self,service_name="es_ingestion"):
        self.service_name=service_name
        Process.__init__(self)
    def run(self):
        config=Config(self.service_name)
        mw=MicroServiceWrapper(config)
        mw.run(ElasticIngestion)