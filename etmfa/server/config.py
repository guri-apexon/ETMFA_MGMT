import yaml
import logging
import os


class Config(object):
    """Parent configuration class."""
    ZMQ_PORT=5556
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    PROPAGATE_EXCEPTIONS = False
    MAX_EXECUTION_WAIT_TIME_HRS=48
    AVG_NUM_CHANGE_PER_LINE=20
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 900,
    }
    
    try:
        file_path="server_config.yaml"
        with open(file_path, 'r') as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
            DFS_UPLOAD_FOLDER = cfg["DFS_UPLOAD_FOLDER"]
            DEBUG = cfg["DEBUG"]
            SQLALCHEMY_DATABASE_URI = cfg["SQLALCHEMY_DATABASE_URI"]
            CDC_OMIT_IP_LIST = cfg["CDC_OMIT_IP_LIST"]
            ENABLE_LOCAL_MODE = cfg["ENABLE_LOCAL_MODE"]
            NO_CDC_REQUIRED_TABLE_LIST = cfg["NO_CDC_REQUIRED_TABLE_LIST"]
            mquser = cfg["mquser"]
            mqpswd = cfg["mqpswd"]
            mqhost = cfg["mqhost"]
            mqport = cfg["mqport"]
            MESSAGE_BROKER_ADDR = "amqp://{0}:{1}@{2}:{3}".format(mquser, mqpswd, mqhost, mqport)
            MESSAGE_BROKER_EXCHANGE = cfg["MESSAGE_BROKER_EXCHANGE"]
            LOGSTASH_HOST = cfg["LOGSTASH_HOST"]
            LOGSTASH_PORT = cfg["LOGSTASH_PORT"]
            AUTH_DETAILS = cfg["AUTH_DETAILS"]
            UNIT_TEST_HEADERS = cfg["UNIT_TEST_HEADERS"]
            WORK_FLOW_RUNNER=cfg['ENABLE_WORK_FLOW_RUNNER']
            UI_HOST_NAME = cfg["UI_HOST_NAME"]
            FROM_EMAIL = cfg["FROM_EMAIL"]
            SMTP_HOST = cfg["SMTP_HOST"]
            SMTP_PORT = cfg["SMTP_PORT"]

    except Exception as exp:
        logging.error("Loading Defaults due to exception when reading yaml from server_config {0}", exp)


class TestConfig(Config):
    """Configurations for Testing."""
    DEBUG = True


class StagingConfig(Config):
    """Configurations for Production."""
    DEBUG = True


class UATConfig(Config):
    """Configurations for UAT."""
    DEBUG = True


class ProductionConfig(Config):
    """Configurations for Production."""
    DEBUG = False


app_config = {
    'local': Config,
    'development': Config,
    'staging': StagingConfig,
    'test': TestConfig,
    'uat': UATConfig,
    'production': ProductionConfig,
}

