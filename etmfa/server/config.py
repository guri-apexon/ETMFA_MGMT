import pymysql
from collections import defaultdict
# import pyodbc


class Config(object):
    """Parent configuration class."""
    DFS_UPLOAD_FOLDER = '//quintiles.net/enterprise/Services/protdigtest/pilot_iqvxml'
    # DFS_UPLOAD_FOLDER = 'C:/Users/q1020640/Desktop/PD/General/pd files/test'
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:Mohan!380@localhost:3306/protocol_dig' #local
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:Mohan!380@/pd_digitalization' #VM?#
    #SQLALCHEMY_DATABASE_URI = 'mysql://root:Mohan!380@/pd_digitalization' #VM?#


    SQLALCHEMY_DATABASE_URI = 'mssql://pd_dev_dbo:$1457abxd@CA2SPDSQL01Q\PDSSQL001D/PD_Dev?driver=SQL+Server'



    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    PROPAGATE_EXCEPTIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 900,
    }

    mquser = 'guest'
    mqpswd = 'guest'
    mqhost = 'ca2spdml01q' #'localhost' #
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


# API endpoint support settings
class _SummaryConfig:
    summary_std_tags = {'KEY_IsSummaryHeader' :'IsSummaryHeader',
                'KEY_IsSummaryElement': 'IsSummaryElement',
                'KEY_IsObjectiveAndEndpoint' : 'IsObjectiveAndEndpoint',
                'KEY_IsInclusionCriteria' : 'IsInclusionCriteria',
                'KEY_IsExclusionCriteria' : 'IsExclusionCriteria',
                'KEY_IsNumberOfParticipants': 'IsNumberOfParticipants',
                'KEY_IsTitle' : 'IsTitle',
                'KEY_IsShortTitle' : 'IsShortTitle',
                'KEY_IsPrimaryObjective' : 'IsPrimaryObjective',
                'KEY_IsSecondaryObjective' : 'IsSecondaryObjective',
                'KEY_IsExploratoryObjective' : 'IsExploratoryObjective',
                'KEY_IsPrimaryEndpoint' : 'IsPrimaryEndpoint',
                'KEY_IsSecondaryEndpoint' : 'IsSecondaryEndpoint',     
                'KEY_IsRationale' : 'IsRationale',
                'KEY_IsDesign': 'IsDesign',
                'KEY_IsBriefSummary': 'IsBriefSummary',
                'KEY_IsInterventionGroups': 'IsInterventionGroups',
                'KEY_IsDataMonitoringCommittee': 'IsDataMonitoringCommittee',
                'KEY_IsSchema': 'IsSchema',
                'KEY_IsSOA': 'IsSOA',     
                'KEY_IsFootNote':'IsFootnote',
                'KEY_TableIndex': 'TableIndex' } 

    subsection_tags = [value for key,value in summary_std_tags.items() if key not in ('KEY_IsSummaryHeader', 'KEY_IsSummaryElement', 'KEY_TableIndex')]


class _GeneralConfig:
    summary_std_tags = _SummaryConfig.summary_std_tags

    soa_std_tags =  {
                     'KEY_HeaderCellIndex':'IsHeaderCell',
                     'KEY_TableIndex':'TableIndex',
                     'KEY_RowIndex':'RowIndex',
                     'KEY_ColIndex':'ColIndex',
                     'KEY_IsFootnote': 'IsFootNote',
                     'KEY_FootNoteLink':'FootNoteLink',
                     'KEY_TableName':'TableName',
                     'KEY_FullText':'FullText'
                     }

    toc_std_tags = { 'KEY_Toc': 'IsToc',
                     'KEY_TableOfTable': 'IsTableOfTable',
                     'KEY_TableOfFigure': 'IsTableOfFigure',
                     'KEY_TableOfAppendix': 'IsTableOfAppendix',
                   }

    other_std_tags = {'KEY_SectionHeaderPrintPage': 'SectionHeaderPrintPage',
                      'KEY_IsSectionHeader': 'IsSectionHeader',
                      'KEY_Default': '',
                    }

    TABLE_INDEX_KEY = 'KEY_TableIndex'
    TABLE_NAME_KEY = 'KEY_TableName'
    FOOTNOTE_KEY = 'KEY_IsFootNote'
    DEFAULT_KEY = ('KEY_Default', '')
    std_tags_dict = defaultdict(lambda: _GeneralConfig.DEFAULT_KEY[1], {**summary_std_tags, **soa_std_tags, **toc_std_tags, **other_std_tags})     

    finalized_doc_prefix = 'FIN_'   


class ModuleConfig:
    """Main module config."""
    GENERAL = _GeneralConfig()
    SUMMARY = _SummaryConfig()
