from etmfa.consts import Consts as consts
from elasticsearch import Elasticsearch
import logging
logger = logging.getLogger(consts.LOGGING_NAME)

def ingest_elastic(host,port,index,es_sec_dict):
    res = True
    try:
        es = Elasticsearch([{'host': host, 'port': port}])
        es.index(index=index, body=es_sec_dict, id=es_sec_dict['AiDocId'])
        logger.info(f"Document was successfully saved in Elastic Search:{es_sec_dict['AiDocId']}")
    except Exception as exc:
        logger.exception(f"Exception received in ingest_elastic, ingestion could not occur:{exc}")
        res = False
    finally:
        es.close()

    return res