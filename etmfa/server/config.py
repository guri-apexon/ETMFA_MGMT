import pymysql
from collections import defaultdict
# import pyodbc


class Config(object):
    """Parent configuration class."""
    DFS_UPLOAD_FOLDER = '//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml'
    #DFS_UPLOAD_FOLDER = '//INKOCWL000200/Users/q1036048/Desktop/__pycache__/PD/pd-management/'
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:Mohan!380@localhost:3306/protocol_dig' #local
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:Mohan!380@/pd_digitalization' #VM?#
    #SQLALCHEMY_DATABASE_URI = 'mysql://root:Mohan!380@/pd_digitalization' #VM?#

    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://pd_dev_dbo:$1457abxd@CA2SPDSQL01Q\PDSSQL001D/PD_Dev?driver=ODBC+Driver+17+for+SQL+Server'



    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    PROPAGATE_EXCEPTIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 900,
    }

    mquser = 'guest'
    mqpswd = 'guest'
    mqhost = 'ca2spdml01q'
    mqport = 5672
    MESSAGE_BROKER_ADDR = "amqp://{0}:{1}@{2}:{3}".format(mquser, mqpswd, mqhost, mqport)
    MESSAGE_BROKER_EXCHANGE = 'PD'
    LOGSTASH_HOST = 'ca2spdml01q'
    LOGSTASH_PORT = 5959


# class DevelopmentConfig(Config):
#     """Configurations for Development."""
#     DEBUG = True
#     host = 'moruorldb113vd'
#     port = 1521
#     sid = 'TMFMLDEV'
#     user = 'TMF_CLASSIFY1'
#     password = 'd3c0d3_12'
#     # sid = cx_Oracle.makedsn(host, port, sid=sid)
#     SQLALCHEMY_DATABASE_URI = 'oracle://{user}:{password}@{sid}'.format(user=user, password=password, sid=sid)
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     PRESERVE_CONTEXT_ON_EXCEPTION = False
#     PROPAGATE_EXCEPTIONS = False
#     SQLALCHEMY_ENGINE_OPTIONS = {
#         "pool_pre_ping": True,
#         "pool_recycle": 900,
#     }
#     mquser = 'guest'
#     mqpswd = 'guest'
#     mqhost = 'rabbitmq-ai-etmfa-dev.work.iqvia.com'  # load balancer IP of RabbitMQ cluster
#     mqport = 5672
#     MESSAGE_BROKER_ADDR = "amqp://{0}:{1}@{2}:{3}".format(mquser, mqpswd, mqhost, mqport)
#     MESSAGE_BROKER_EXCHANGE = 'eTMFA'
#     LOGSTASH_HOST = 'morsetmfml01d'
#     LOGSTASH_PORT = 5959


# class SVTConfig(Config):
#     """Configurations for Testing."""
#     DEBUG = True
#     host = 'moruorldb113vd'
#     port = 1521
#     sid = 'TMFMLDEV'
#     user = 'TMF_CLASSIFY'
#     password = 'tMfA3lod'
#     sid = cx_Oracle.makedsn(host, port, sid=sid)
#     SQLALCHEMY_DATABASE_URI = 'oracle://{user}:{password}@{sid}'.format(user=user, password=password, sid=sid)
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     PRESERVE_CONTEXT_ON_EXCEPTION = False
#     PROPAGATE_EXCEPTIONS = False
#     SQLALCHEMY_ENGINE_OPTIONS = {
#         "pool_pre_ping": True,
#         "pool_recycle": 900,
#     }
#     mquser = 'guest'
#     mqpswd = 'guest'
#     mqhost = 'morsetmfhs06d'
#     mqport = 5672
#     MESSAGE_BROKER_ADDR = "amqp://{0}:{1}@{2}:{3}".format(mquser, mqpswd, mqhost, mqport)
#     MESSAGE_BROKER_EXCHANGE = 'eTMFA'
#     LOGSTASH_HOST = 'morsetmfhs06d'
#     LOGSTASH_PORT = 5959


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
    # 'svt': SVTConfig,
    'uat': UATConfig,
    'production': ProductionConfig,
}
