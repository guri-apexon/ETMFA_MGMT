import logging
from etmfa.consts.constants import ModuleConfig, QcStatus
from etmfa.utilities.data_extractor_utils import get_redaction_entities, align_redaction_with_subtext
from etmfa.utilities.elastic_utilities import ingest_elastic
from datetime import datetime
from etmfa.consts import Consts as consts
from etmfa.db.models.pd_protocol_metadata import MetaDataTableHelper

logger = logging.getLogger(consts.LOGGING_NAME)

"""
Keys for Extraction from DocumentLinks
"""
es_toc_sec_pat = [
    'IsInclusionCriteria',
    'IsExclusionCriteria',
    'IsObjectives',
    'IsEndpoints',
    'IsAdverseEvents',
    'IsSeriousAdverseEvents'
]

summary_sec_pat = ['IsObjectiveAndEndpoint',
                   'IsInclusionCriteria',
                   'IsExclusionCriteria',
                   'IsNumberOfParticipants',
                   'IsTitle',
                   'IsShortTitle',
                   'IsPrimaryObjective',
                   'IsSecondaryObjective',
                   'IsExploratoryObjective',
                   'IsPrimaryEndpoint',
                   'IsSecondaryEndpoint',
                   'IsRationale',
                   'IsDesign',
                   'IsBriefSummary',
                   'IsInterventionGroups',
                   'IsDataMonitoringCommittee',
                   'IsSchema']

ling_es_mapping = {
    "ProtocolTitle": "ProtocolTitle",
    "short_title": "ShortTitle",
    "amendment_number": "AmendmentNumber",
    "phase": "phase",
    "molecule_device": "MoleculeDevice",
    "sponsor": "SponsorName",
    "sponsor_address": "SponsorAddress",
    "drug": "Drug",
    "approval_date": "approval_date",
    "ProtocolVersion": "VersionNumber",
    "version_date": "VersionDate",
    "blinding": "Blinding",
    "compound": "Compound",
    "control": "Control",
    "investigator": "Investigator",
    "study_id": "StudyId",
    "number_of_subjects": "NumberOfSubjects",
    "participant_age": "ParticipantAge",
    "participant_sex": "ParticipantSex",
    "exclusion_section": "ExclusionSection",
    "inclusion_section": "InclusionSection",
    "indication": "Indication",
    "objectives_section": "ObjectivesSection",
    "population": "Population",
    "entities_in_assessments": "EntitiesInAssessments",
    "soa_epochs": "SoaEpochs",
    "soa_footnotes": "SoaFootnote"
}


def save_elastic_doc(host, port, index, es_sec_dict):
    if es_sec_dict:
        return ingest_elastic(host, port, index, es_sec_dict)


def ingest_doc_elastic(iqv_document, search_df):
    """
        searching document id in elastic 
        iqv_document: requested document
        search_df:  dict format cpt section data contians content, type, font_info details
    """
    current_timestamp = datetime.utcnow()
    current_utc_num_format = current_timestamp.strftime("%Y%m%d%H%M%S")
    es_sec_dict = dict()
    summary_entities = dict()
    search_rollup_column = ModuleConfig.GENERAL.SEARCH_ROLLUP_COLUMN

    try:
        if iqv_document.id:
            es_sec_dict['AiDocId'] = iqv_document.id
    except Exception as exc:
        logger.exception(f"Exception received in ingest_doc_elastic, AIDocId not present:{exc}")

    # CPT file content extraction
    try:
        if search_df is not None and len(search_df) > 0:
            rollup_df = search_df
            rollup_df = rollup_df.groupby(search_rollup_column)['content'].apply(list).reset_index()
            rollup_df['content'] = rollup_df['content'].apply(lambda x: ' '.join(x))
            toc_dict = {hdr[search_rollup_column]: hdr['content'] for hdr in rollup_df.to_dict(orient='records')}
            es_sec_dict.update(toc_dict)
        else:
            logger.warning("No data from digitized document inserted to elastic search. search_df is empty")

    except Exception as exc:
        logger.exception(f"Exception received in rollup stage : {exc}")

    # Populating intake fields
    try:
        intake_dict = dict()
        es_sec_dict['uploadDate'] = iqv_document.dateTimeUploaded
        es_sec_dict['SourceFileName'] = iqv_document.originalSourceFilename.split('\\')[-1]
        es_sec_dict['documentPath'] = iqv_document.DropBoxDir
        es_sec_dict['is_active'] = 1
        for IQVDocumentFeedbackResults in iqv_document.IQVDocumentFeedbackResultsList:
            intake_dict['ProtocolNo'] = IQVDocumentFeedbackResults.protocol.strip()
            intake_dict['SourceFileName'] = IQVDocumentFeedbackResults.source_filename.split("\\")[-1]
            intake_dict['DocumentStatus'] = IQVDocumentFeedbackResults.document_status.strip()
            intake_dict['VersionNumber'] = IQVDocumentFeedbackResults.version_number.strip()
            intake_dict['UserId'] = IQVDocumentFeedbackResults.user_id.strip()
            intake_dict['UserModified'] = ""  # IQVDocumentFeedbackResults.user_id
            intake_dict['ProjectId'] = IQVDocumentFeedbackResults.project_id.strip()
            intake_dict[
                'IsAmendment'] = IQVDocumentFeedbackResults.amendment_number.strip()  # This is Yes, No Flag from UI
            intake_dict['Indication'] = IQVDocumentFeedbackResults.indication.strip()
            intake_dict['uploadDate'] = IQVDocumentFeedbackResults.date_time_stamp.strip()  # YYYYMMDDHHMMSS
            intake_dict['TimeCreated'] = ""  # IQVDocumentFeedbackResults.date_time_stamp # YYYYMMDDHHMMSS
            intake_dict['TimeUpdated'] = ""  # IQVDocumentFeedbackResults.date_time_stamp # YYYYMMDDHHMMSS
            intake_dict['Environment'] = IQVDocumentFeedbackResults.environment.strip()
            intake_dict['SourceSystem'] = IQVDocumentFeedbackResults.source_system.strip()
            intake_dict['StudyStatus'] = IQVDocumentFeedbackResults.study_status.strip()
            intake_dict['DraftVersion'] = IQVDocumentFeedbackResults.draft_number.strip()
        for sec in intake_dict:
            if sec not in es_sec_dict or es_sec_dict[sec] == '':
                es_sec_dict[sec] = intake_dict[sec]
        es_sec_dict['qcStatus'] = MetaDataTableHelper().get_qc_status(iqv_document.id)
        es_sec_dict['QC_Flag'] = False
        es_sec_dict['TimeCreated'] = current_utc_num_format
        es_sec_dict['TimeUpdated'] = current_utc_num_format

    except Exception as exc:
        logger.exception(f"Exception received in ingest_doc_elastic, intake field extraction:{exc}")

    # Populating Linguamatics fields
    try:
        linguamatics_op_dict = {
            "ProtocolTitle": "",  # yes
            "molecule_device":"",
            "amendment_number": "",  # yes
            "compound": "",  # yes
            "control": "",  # yes
            "drug": "",  # yes, nothing but intervention name
            "investigator": "",  # yes
            "short_title": "",  # yes
            "sponsor_address": "",  # yes
            "study_id": "",  # yes
            "version_date": "",  # yes
            "ProtocolVersion": "",  # yes
            "phase": "",  # yes
            "sponsor": "",  # yes
            "approval_date": "",  # yes
            "blinding": "",  # yes
            "number_of_subjects": "",  # yes
            "participant_age": "",  # yes
            "participant_sex": "",  # yes
            "exclusion_section": "",
            "inclusion_section": "",
            "indication": "",
            "objectives_section": "",
            "population": "",
            "entities_in_assessments": "",
            "soa_epochs": "",
            "soa_footnotes": ""
        }

        for kv in iqv_document.Properties:
            if kv.key in linguamatics_op_dict and linguamatics_op_dict[kv.key] == '':
                linguamatics_op_dict[kv.key] = kv.value.strip()
                _, redaction_entities = get_redaction_entities(level_roi=kv)
                _, subtext_redaction_entities = align_redaction_with_subtext(kv.value, redaction_entities)
                if subtext_redaction_entities:
                    summary_entities[kv.key] = subtext_redaction_entities

        for key in ling_es_mapping:
            if ling_es_mapping[key] in es_sec_dict and linguamatics_op_dict[key] != '':
                es_sec_dict[ling_es_mapping[key]] = linguamatics_op_dict[key]
            elif ling_es_mapping[key] not in es_sec_dict:
                es_sec_dict[ling_es_mapping[key]] = linguamatics_op_dict[key]

        if (es_sec_dict['approval_date'].isnumeric() and len(es_sec_dict['approval_date']) != 8) or (
        not es_sec_dict['approval_date'].isnumeric()):
            es_sec_dict['approval_date'] = ''

    except Exception as exc:
        logger.exception(f"Exception received in ingest_doc_elastic, intake field extraction:{exc}")

    return es_sec_dict, summary_entities
