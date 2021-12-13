import yaml
import logging
from etmfa.consts import Consts as consts

logger = logging.getLogger(consts.LOGGING_NAME)

class Config(object):
    """Parent configuration class."""

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    PROPAGATE_EXCEPTIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 900,
    }
    try:
        with open("server_config.yaml", 'r') as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
            DFS_UPLOAD_FOLDER = cfg["DFS_UPLOAD_FOLDER"]
            DEBUG = cfg["DEBUG"]
            SQLALCHEMY_DATABASE_URI = cfg["SQLALCHEMY_DATABASE_URI"]
            mquser = cfg["mquser"]
            mqpswd = cfg["mqpswd"]
            mqhost = cfg["mqhost"]
            mqport = cfg["mqport"]
            MESSAGE_BROKER_ADDR = "amqp://{0}:{1}@{2}:{3}".format(mquser, mqpswd, mqhost, mqport)
            MESSAGE_BROKER_EXCHANGE = cfg["MESSAGE_BROKER_EXCHANGE"]
            LOGSTASH_HOST = cfg["LOGSTASH_HOST"]
            LOGSTASH_PORT = cfg["LOGSTASH_PORT"]

            PD_UI_LINK = cfg["PD_UI_LINK"]
            AUTH_DETAILS = cfg["AUTH_DETAILS"]
            UNIT_TEST_HEADERS = cfg["UNIT_TEST_HEADERS"]

    except Exception as exp:
        logger.error("Loading Defaults due to exception when reading yaml from server_config {0}", exp)


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
