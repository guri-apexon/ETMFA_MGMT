import cx_Oracle

class Config(object):
    """Parent configuration class."""
    DEBUG = False
    MESSAGE_BROKER_ADDR = "amqp://guest:guest@localhost:5672"
    MESSAGE_BROKER_EXCHANGE = 'eTMFA'
    LOGSTASH_HOST = 'morsetmfml01d'
    LOGSTASH_PORT = 5959

class DevelopmentConfig(Config):
    """Configurations for Development."""
    DEBUG = True
    host = 'moruorldb113vd'
    port = 1521
    sid = 'TMFMLDEV'
    user = 'TMF_CLASSIFY1'
    password = 'd3c0d3_12'
    sid = cx_Oracle.makedsn(host, port, sid=sid)
    SQLALCHEMY_DATABASE_URI = 'oracle://{user}:{password}@{sid}'.format(user=user, password=password, sid=sid)
    mquser = 'guest'
    mqpswd = 'guest'
    mqhost = 'morsetmfml01d'
    mqport = 5672
    MESSAGE_BROKER_ADDR = "amqp://{0}:{1}@{2}:{3}".format(mquser, mqpswd, mqhost, mqport)
    MESSAGE_BROKER_EXCHANGE = 'eTMFA'
    LOGSTASH_HOST = 'morsetmfml01d'
    LOGSTASH_PORT = 5959

class SVTConfig(Config):
    """Configurations for Testing."""
    DEBUG = True
    host = 'moruorldb113vd'
    port = 1521
    sid = 'TMFMLDEV'
    user = 'TMF_CLASSIFY'
    password = 'tMfA3lod'
    sid = cx_Oracle.makedsn(host, port, sid=sid)
    SQLALCHEMY_DATABASE_URI = 'oracle://{user}:{password}@{sid}'.format(user=user, password=password, sid=sid)
    mquser = 'guest'
    mqpswd = 'guest'
    mqhost = 'morsetmfhs06d'
    mqport = 5672
    MESSAGE_BROKER_ADDR = "amqp://{0}:{1}@{2}:{3}".format(mquser, mqpswd, mqhost, mqport)
    MESSAGE_BROKER_EXCHANGE = 'eTMFA'
    LOGSTASH_HOST = 'morsetmfhs06d'
    LOGSTASH_PORT = 5959


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
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'test': TestConfig,
    'svt': SVTConfig,
    'uat': UATConfig,
    'production': ProductionConfig,
}
