

from mq_service.config import Config
from microservices.es_ms import ElasticIngestion

def test_elastic_ingestion():
    cc=Config('simple')
    fn=ElasticIngestion(cc)
    data={'final':{'docId':'012fd828-a027-46bc-97f9-4d6168c18ec0'}}
    msg=fn.on_callback(data)
    assert msg!=None