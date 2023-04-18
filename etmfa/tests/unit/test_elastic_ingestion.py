

from mq_service.config import Config
from microservices.es_ms import ElasticIngestion
def test_elastic_ingestion():
    cc=Config('simple')
    fn=ElasticIngestion(cc)
    data={'final':{'docId':'31935a9a-0732-47fb-ab97-786703333c5d'}}
    msg=fn.on_callback(data)
    assert msg!=None