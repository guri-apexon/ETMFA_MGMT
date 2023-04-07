
import yaml
import logging
import os


class Config(object):
    """Parent configuration class."""

    def __init__(self, service_name, error_queue='documentprocessing_error'):
        self.SERVICE_NAME = service_name
        self.INPUT_QUEUE_NAME = service_name+'_request'
        self.OUTPUT_QUEUE_NAME = service_name+'_complete'
        self.ERROR_QUEUE_NAME = error_queue

    CONTEXT_MAX_ACTIVE_TIME = 900  # 15*60
    SERVICE_THREAD_WAIT_TIME = 15*60  # 60sec

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    PROPAGATE_EXCEPTIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 900,
    }
    try:
        file_path = os.path.join("server_config.yaml")
        with open(file_path, 'r') as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
            DEBUG = cfg["DEBUG"]
            SQLALCHEMY_DATABASE_URI = cfg["SQLALCHEMY_DATABASE_URI"]
            mquser = cfg["mquser"]
            mqpswd = cfg["mqpswd"]
            mqhost = cfg["mqhost"]
            mqport = cfg["mqport"]
            MESSAGE_BROKER_ADDR = "amqp://{0}:{1}@{2}:{3}".format(
                mquser, mqpswd, mqhost, mqport)
            MESSAGE_BROKER_EXCHANGE = cfg["MESSAGE_BROKER_EXCHANGE"]
            LOGSTASH_HOST = cfg["LOGSTASH_HOST"]
            LOGSTASH_PORT = cfg["LOGSTASH_PORT"]
            ELASTIC_DETAILS=cfg["ELASTIC_DETAILS"]

    except Exception as exp:
        logging.error(
            "Loading Defaults due to exception when reading yaml from server_config {0}", exp)
