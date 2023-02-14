import datetime
import logging
import os
import json

from etmfa.db.db import db_context
from etmfa.consts import Consts as consts
from etmfa.db.models.pd_protocol_data import Protocoldata
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db.models.pd_protocol_qcdata import Protocolqcdata
from etmfa.db.models.pd_protocol_summary_entities import ProtocolSummaryEntities

logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"

def update_protocol_metadata(id, FeedbackRunId, finalattributes):
    protocolmetadata = db_context.session.query(PDProtocolMetadata).filter(PDProtocolMetadata.id == id).first()
    if FeedbackRunId == 0:
        protocolmetadata.protocolTitle = finalattributes['ProtocolTitle']
        protocolmetadata.shortTitle = finalattributes['ShortTitle']
        protocolmetadata.phase = finalattributes['phase']
        protocolmetadata.approvalDate = (None if finalattributes['approval_date'] == '' else finalattributes['approval_date'])
        version_number = finalattributes.get('VersionNumber', '').strip()
        if version_number:
            protocolmetadata.versionNumber = version_number    
    protocolmetadata.runId = FeedbackRunId  # Only need to update this field during rerun in metadatatable

def upsert_protocol_data(FeedbackRunId, finalattributes):
    protocoldata = Protocoldata()
    protocoldata.id = finalattributes['AiDocId']
    protocoldata.userId = finalattributes['UserId']
    protocoldata.fileName = finalattributes['SourceFileName']
    protocoldata.documentFilePath = finalattributes['documentPath']

    protocoldata.isActive = True
    protocoldata.iqvdataToc = str(json.dumps(finalattributes['toc']))
    protocoldata.iqvdataSoa = str(json.dumps(finalattributes['soa']))
    protocoldata.iqvdataSoaStd = (
        None if finalattributes['normalized_soa'] == '' or finalattributes['normalized_soa'] is None else str(
            json.dumps(finalattributes['normalized_soa'])))
    protocoldata.iqvdataSummary = str(json.dumps(finalattributes['summary']))
    current_time = datetime.datetime.utcnow()
    protocoldata.timeUpdated = current_time
    if FeedbackRunId == 0:
        protocoldata.timeCreated = current_time

    return protocoldata


def upsert_protocol_qcdata(FeedbackRunId, finalattributes):
    protocolqcdata = Protocolqcdata()
    protocolqcdata.id = finalattributes['AiDocId']
    protocolqcdata.userId = finalattributes['UserId']
    protocolqcdata.fileName = finalattributes['SourceFileName']
    protocolqcdata.documentFilePath = finalattributes['documentPath']

    protocolqcdata.isActive = False
    protocolqcdata.iqvdataToc = str(json.dumps(finalattributes['toc']))
    protocolqcdata.iqvdataSoa = str(json.dumps(finalattributes['soa']))
    protocolqcdata.iqvdataSoaStd = (
        None if finalattributes['normalized_soa'] == '' or finalattributes['normalized_soa'] is None \
            else str(json.dumps(finalattributes['normalized_soa'])))
    protocolqcdata.iqvdataSummary = str(json.dumps(finalattributes['summary']))
    current_time = datetime.datetime.utcnow()
    protocolqcdata.timeUpdated = current_time
    if FeedbackRunId == 0:
        protocolqcdata.timeCreated = current_time

    return protocolqcdata

def upsert_summary_entities(FeedbackRunId, finalattributes):
    protocol_summary_entities = ProtocolSummaryEntities()
    protocol_summary_entities.aidocId = finalattributes['AiDocId']
    protocol_summary_entities.runId = FeedbackRunId
    protocol_summary_entities.source = 'LM' if FeedbackRunId == 0 else 'FEEDBACK_RUN'
    protocol_summary_entities.iqvdataSummaryEntities = str(json.dumps(finalattributes.get('summary_entities', {})))
    current_time = datetime.datetime.utcnow()
    protocol_summary_entities.timeUpdated = current_time
    if FeedbackRunId > 0:
        protocol_summary_entities.timeCreated = current_time

    return protocol_summary_entities