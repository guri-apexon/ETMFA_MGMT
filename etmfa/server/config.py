class Config(object):
    """Parent configuration class."""
    DFS_UPLOAD_FOLDER = '//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml'
    DEBUG = True

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

    PD_UI_LINK = "https://protocoldigitalization-ui.work.iqvia.com/dashboard"

    # User Authentication
    AUTH_DETAILS = {'ypd_api_dev': '$pbkdf2-sha256$8000$yfn/n3Oudc75Pw$A7BQFNmip/A/VqQcQphknV32gdGmFHzq56jjBHN0lXY',
                    'ypd_unit_test': '$pbkdf2-sha256$8000$MqZ0jnGO8d77fw$7tT5b7tJbmV0ofz97G75mAUPeDrf5O8ythuRfO6vrWo'}

    UNIT_TEST_HEADERS = {"X-API-KEY": "ypd_unit_test:!53*URTa$k1j4t^h2~uSseatnai@nr"}

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
