import os
from urllib.parse import quote

class Config(object):
    """Parent configuration class."""
    DEBUG = False
    params = quote("SERVER=.;DATABASE=TMSDEV;Integrated Security=True;DRIVER={SQL Server};")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)
    SWAGGER_UI_DOC_EXPANSION = "RESTPLUS_SWAGGER_UI_DOC_EXPANSION"
    MESSAGE_BROKER_ADDR = "amqp://guest:guest@localhost"
    MESSAGE_BROKER_EXCHANGE = 'TMS'
    GET_LANGUAGES_ADDR = 'http://localhost:8204/api/translate/languagePairs'
    LOGSTASH_HOST = 'usadc-vstmswd02'
    LOGSTASH_PORT = 5004

class DevelopmentConfig(Config):
    """Configurations for Development."""
    DEBUG = True
    params = quote("SERVER=.;DATABASE=TMSDEV;Integrated Security=True;DRIVER={SQL Server};")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)
    MESSAGE_BROKER_ADDR = "amqp://guest:guest@localhost"
    GET_LANGUAGES_ADDR = 'http://usadc-vstmsad01:8204/api/translate/languagePairs'

class TestConfig(Config):
    """Configurations for Testing."""
    DEBUG = True
    params = quote("SERVER=USADC-VSSQLA0\SSQL01;DATABASE=TMSTST;UID=APP_TMSTST;PWD=app$tmstst;DRIVER={SQL Server};")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)
    GET_LANGUAGES_ADDR = 'http://USADC-VSTMSTA02:8204/api/translate/languagePairs'
    MESSAGE_BROKER_ADDR = "amqp://guest:guest@USADC-VSTMSTW01"
    LOGSTASH_HOST = 'USADC-VSTMSTW01'

class SVTConfig(Config):
    """Configurations for Testing."""
    DEBUG = True
    params = quote("SERVER=USADC-VSSQLA0\SSQL04;DATABASE=TMSSVT;UID=APP_TMSSVT;PWD=APP$TMSSVT1;DRIVER={SQL Server};")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)
    MESSAGE_BROKER_ADDR = "amqp://guest:guest@MORSSTMSW001"
    LOGSTASH_HOST = 'USADC-VSTMSTW01'
    GET_LANGUAGES_ADDR = 'https://morsstmsw002:8204/api/translate/languagePairs'


class StagingConfig(Config):
    """Configurations for Production."""
    DEBUG = True
    params = quote("SERVER=USADC-VSSQLA0\SSQL03;DATABASE=TMSDEV;UID=APP_TMSDEV;PWD=app$tmsdev;DRIVER={SQL Server};")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)
    MESSAGE_BROKER_ADDR = "amqp://guest:guest@usadc-vstmsad01"
    GET_LANGUAGES_ADDR = 'http://usadc-vstmsad01:8204/api/translate/languagePairs'

class UATConfig(Config):
    """Configurations for UAT."""
    DEBUG = True
    params = quote("SERVER=USADC-VSSQLA0\SSQL05;DATABASE=TMS_UAT;UID=APP_TMSUAT;PWD=APP$TMSUAT1;DRIVER={SQL Server};")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)
    MESSAGE_BROKER_ADDR = "amqp://guest:guest@dcmor1stmsuw01"
    LOGSTASH_HOST = 'USADC-VSTMSTW01'
    GET_LANGUAGES_ADDR = 'https://dcmor1stmsuw02:8204/api/translate/languagePairs'

class ProductionConfig(Config):
    """Configurations for Production."""
    DEBUG = False
    params = quote("SERVER=USADC-VSSQLAP02\SSQL01;DATABASE=TMSPROD;UID=APP_TMSDEV;PWD=app$tmsdev;DRIVER={SQL Server};")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)
    MESSAGE_BROKER_ADDR = 'dcmor1stmsuw01'
    LOGSTASH_HOST = 'dcmor1stmsuw01'
    GET_LANGUAGES_ADDR = 'https://dcmor1stmsua01:8204/api/translate/languagePairs'


app_config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'test': TestConfig,
    'svt': SVTConfig,
    'uat': UATConfig,
    'production': ProductionConfig,
}
