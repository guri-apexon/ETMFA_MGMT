

from mq_service.config import Config
from microservices.es_ms import ElasticIngestion
def test_elastic_ingestion():
    cc=Config('simple')
    fn=ElasticIngestion(cc)
    data={'final':{'docId':'a9286bc5-6b90-48af-9b0c-c365119e69c8'}}
    msg=fn.on_callback(data)
    assert msg!=None