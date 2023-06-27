

from mq_service.config import Config
from microservices.es_ms import ElasticIngestion
def test_elastic_ingestion():
    cc=Config('simple')
    fn=ElasticIngestion(cc)
    data={'final':{'docId':'94770170-19c2-4a3e-9505-7e6b9c683b3d'}}
    msg=fn.on_callback(data)
    assert msg!=None