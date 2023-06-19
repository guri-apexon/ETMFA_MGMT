import re
import json
from collections import defaultdict
import pandas as pd
from enum import Enum, unique, auto

# # Profiles
USERROLE_REDACTPROFILE_MAP = {"primary": "profile_1", "secondary": "profile_0", "default": "profile_0"}
REGEX_SPECIAL_CHAR_REPLACE = re.compile('([^a-zA-Z0-9])')

GENRE_ENTITY_NAME = 'entity'
GENRE_ATTRIBUTE_NAME = 'attributes'
GENRE_ACTION_NAME = 'action'
GENRE_SECTION_NAME = 'section'
GENRE_ATTRIBUTE_ENTITY = "attributes_entity"
REDACT_ATTR_STR = '~REDACTED~'
REDACT_PARAGRAPH_STR = '~REDACTED~'

ACCORDIAN_DOC_ID = '1' * 10
DUPLICATION_ERROR = "duplication error"

# Redaction
REDACTION_FLAG = {"profile_1": False, "profile_0": True}
EXCLUDE_REDACT_PROPERTY_FLAG = {"profile_1": False, "profile_0": True}
HIDE_TABLE_JSON_FLAG = {"profile_1": True, "profile_0": True}
RETURN_REFRESHED_TABLE_HTML_FLAG = {"profile_1": False, "profile_0": True}

# # Redaction Footnotes
FOOTNOTES_TEXT = "Text"
FOOTNOTES_ENTITIES = "entities"
FOOTNOTES_START_INDEX = "start_idx"
FOOTNOTES_END_INDEX = "end_idx"
FOOTNOTES_KEY = "Key"
FOOTNOTE_STR = "FootnoteText"

# # Legacy Protocol Configuration
LEGACY_PROTOCOL_UPLOAD_DATE = "2021-09-19"

LEGACY_QUEUE_NAMES = ['triage', 'digitizer1', 'digitizer2', 'i2e_omop_update', 'digitizer2_omopupdate', 'extraction']

# WF to be excluded
EXCLUDED_WF = ['digitization', 'full_flow', 'email_notification']
DEFAULT_WORKFLOW_NAME = "Default_Workflow"
# used in LM mapped fields
STUDY_ASSESSMENT_AND_PROCEDURE = 'Study Assessments And Procedure'
PATIENT_COMPLEXITY = 'Patient Complexity'
SUMMARY_EXTENDED = 'summary_extended'
WORKFLOW_ORDER = ["triage", "digitizer1",
                  "digitizer2", "extraction",
                  "digitizer2_omopgenerate",
                  "digitizer2_normsoa",
                  "i2e_omop_update",
                  "digitizer2_omopupdate",
                  "digitizer2_compare",
                  "meta_tagging", "meta_extraction", "analyzer", "es_ingestion",
                  "email_notification"]

@unique
class QcStatus(Enum):
    """PD Quality Check status"""
    NOT_STARTED = 'QC_NOT_STARTED'
    QC1 = 'QC1'
    QC2 = 'QC2'
    COMPLETED = 'QC_COMPLETED'


class _SummaryConfig:
    summary_std_tags = {'KEY_IsSummaryHeader': 'IsSummaryHeader',
                        'KEY_IsSummaryElement': 'IsSummaryElement',
                        'KEY_IsObjectiveAndEndpoint': 'IsObjectiveAndEndpoint',
                        'KEY_IsInclusionCriteria': 'IsInclusionCriteria',
                        'KEY_IsExclusionCriteria': 'IsExclusionCriteria',
                        'KEY_IsNumberOfParticipants': 'IsNumberOfParticipants',
                        'KEY_IsTitle': 'IsTitle',
                        'KEY_IsShortTitle': 'IsShortTitle',
                        'KEY_IsPrimaryObjective': 'IsPrimaryObjective',
                        'KEY_IsSecondaryObjective': 'IsSecondaryObjective',
                        'KEY_IsExploratoryObjective': 'IsExploratoryObjective',
                        'KEY_IsPrimaryEndpoint': 'IsPrimaryEndpoint',
                        'KEY_IsSecondaryEndpoint': 'IsSecondaryEndpoint',
                        'KEY_IsRationale': 'IsRationale',
                        'KEY_IsDesign': 'IsDesign',
                        'KEY_IsBriefSummary': 'IsBriefSummary',
                        'KEY_IsInterventionGroups': 'IsInterventionGroups',
                        'KEY_IsDataMonitoringCommittee': 'IsDataMonitoringCommittee',
                        'KEY_IsSchema': 'IsSchema',
                        'KEY_IsSOA': 'IsSOA',
                        'KEY_IsFootNote': 'IsFootnote',
                        'KEY_TableIndex': 'TableIndex'}

    subsection_tags = [value for key, value in summary_std_tags.items() if
                       key not in ('KEY_IsSummaryHeader', 'KEY_IsSummaryElement', 'KEY_TableIndex')]

    summary_key_list = {
        "protocol_name": "Protocol Name", "protocol_number": "Protocol Number", "protocol_title": "Protocol Title",
        "protocol_title_short": "Protocol Title Short", "is_amendment": "Is Amendment",
        "amendment_number": "Amendment Number",
        "trial_phase": "Trial Phase", "sponsor": "Sponsor", "sponsor_address": "Sponsor Address", "drug": "Drug",
        "approval_date": "Approval Date", "version_number": "Version Number", "version_date": "Version Date",
        "blinded": "Blinded", "compound_number": "Compound Number", "control": "Control",
        "investigator": "Investigator",
        "study_id": "Study Id", "number_of_subjects": "Number Of Subjects", "participant_age": "Participant Age",
        "participant_sex": "Participant Sex", "exclusion_criteria": "Exclusion Criteria",
        "inclusion_criteria": "Inclusion Criteria", "indication": "Indication",
        "primary_objectives": "Primary Objectives",
        "secondary_objectives": "Secondary Objectives", "study_status": "Study Status",
        "study_population": "Study Population", "endpoints": "Endpoints",
        "trial_type_randomized": "Trial Type Randomized",
        "molecule_device": "Molecule Device"
    }


# db_name,display_name,group_name
LM_MAPPED_FIELDS = {
    'adverse_events': ('adverse_events', 'Adverse Events', 'Adverse Events LM'),
    'serious_adverse_events': ('serious_adverse_events', 'Serious Adverse Events', 'Serious Adverse Events LM'),
    'biopsy': ('biopsy', 'Biopsy', PATIENT_COMPLEXITY),
    'biopsy_list': ('biopsy_list', 'Biopsy List', PATIENT_COMPLEXITY),
    'blood_draw': ('blood_draw', 'Blood Draw', PATIENT_COMPLEXITY),
    'blood_draw_list': ('blood_draw_list', 'Blood Draw List', PATIENT_COMPLEXITY),
    'caregiver': ('caregiver', 'Caregiver', PATIENT_COMPLEXITY),
    'caregiver_list': ('caregiver_list', 'Caregiver List', PATIENT_COMPLEXITY),
    'colonoscopy': ('colonoscopy', 'Colonoscopy', PATIENT_COMPLEXITY),
    'colonoscopy_list': ('colonoscopy_list', 'Colonoscopy List', PATIENT_COMPLEXITY),
    'demographics': ('colonoscopy_list', 'Colonoscopy List', STUDY_ASSESSMENT_AND_PROCEDURE),
    'diary': ('diary', 'Diary', PATIENT_COMPLEXITY),
    'diary_list': ('diary_list', 'Diary List', PATIENT_COMPLEXITY),
    'discontinue_treatment': ('discontinue_treatment', 'Discontinue Treatment', PATIENT_COMPLEXITY),
    'discontinue_treatment_list': ('discontinue_treatment_list', 'Discontinue Treatment List', PATIENT_COMPLEXITY),
    'ecg': ('ecg', 'ECG', STUDY_ASSESSMENT_AND_PROCEDURE),
    'endoscopy': ('endoscopy', 'Endoscopy', PATIENT_COMPLEXITY),
    'endoscopy_list': ('endoscopy_list', 'Endoscopy List', PATIENT_COMPLEXITY),
    'freq_pro': ('freq_pro', 'Freq Pro', PATIENT_COMPLEXITY),
    'imaging_ct': ('imaging_ct', 'Imaging CT', PATIENT_COMPLEXITY),
    'imaging_ct_list': ('imaging_ct', 'Imaging CT', PATIENT_COMPLEXITY),
    'imaging_dexa': ('imaging_dexa', 'Imaging Dexa', PATIENT_COMPLEXITY),
    'imaging_dexa_list': ('imaging_dexa_list', 'Imaging Dexa List', PATIENT_COMPLEXITY),
    'imaging_mammogram': ('imaging_mammogram', 'Imaging Mammogram', PATIENT_COMPLEXITY),
    'imaging_mammogram_list': ('imaging_mammogram_list', 'Imaging Mammogram List', PATIENT_COMPLEXITY),
    'imaging_mri': ('imaging_mri', 'Imaging MRI', PATIENT_COMPLEXITY),
    'imaging_mri_list': ('imaging_mri_list', 'Imaging MRI_List', PATIENT_COMPLEXITY),
    'imaging_pet': ('imaging_pet', 'Imaging Pet', PATIENT_COMPLEXITY),
    'imaging_pet_list': ('imaging_pet_list', 'Imaging Pet List', PATIENT_COMPLEXITY),
    'imaging_ultrasound': ('imaging_ultrasound', 'Imaging Ultrasound', PATIENT_COMPLEXITY),
    'imaging_ultrasound_list': ('imaging_ultrasound_list', 'Imaging Ultrasound List', PATIENT_COMPLEXITY),
    'imaging_xray': ('imaging_xray', 'Imaging Xray', PATIENT_COMPLEXITY),
    'imaging_xray_list': ('imaging_xray_list', 'Imaging Xray List', PATIENT_COMPLEXITY),
    'injectable': ('injectable', 'Injectable', PATIENT_COMPLEXITY),
    'injectable_list': ('injectable_list', 'Injectable List', PATIENT_COMPLEXITY),
    'inpatient': ('inpatient', 'Inpatient', PATIENT_COMPLEXITY),
    'inpatient_list': ('inpatient_list', 'Inpatient List', PATIENT_COMPLEXITY),
    'lumbar_puncture': ('lumbar_puncture', 'Lumbar Puncture', PATIENT_COMPLEXITY),
    'lumbar_puncture_list': ('lumbar_puncture_list', 'Lumbar Puncture List', PATIENT_COMPLEXITY),
    'vital_signs': ('vital_signs', 'Vital Signs', STUDY_ASSESSMENT_AND_PROCEDURE),
    'total_num_pro': ('total_num_pro', 'Total Num Pro', STUDY_ASSESSMENT_AND_PROCEDURE),
    'total_num_site_visit': ('total_num_site_visit', 'Total Num Site Visit', STUDY_ASSESSMENT_AND_PROCEDURE),
    'total_num_site_visit_list': (
    'total_num_site_visit_list', 'Total Num Site Visit List', STUDY_ASSESSMENT_AND_PROCEDURE),
    'exclusion_section': ('exclusionCriteria', 'Exclusion Criteria', SUMMARY_EXTENDED),
    'inclusion_section': ('inclusionCriteria', 'Inclusion Criteria', SUMMARY_EXTENDED),
    'indication': ('indication', 'Indication', SUMMARY_EXTENDED),
    'number_of_subjects': ('numOfSubjects', 'Number Of Subjects', SUMMARY_EXTENDED),
    'objectives_section': ('primaryObjectives', 'Primary Objectives', SUMMARY_EXTENDED),
    'participant_age': ('participantAge', 'Participant Age', SUMMARY_EXTENDED),
    'participant_sex': ('participantSex', 'Participant Sex', SUMMARY_EXTENDED),
    'blinding': ('blinded', 'Blinded', SUMMARY_EXTENDED),
    'phase': ('phase', 'Trial Phase', SUMMARY_EXTENDED),
    'ProtocolNumber': ('protocol', 'Protocol Number', SUMMARY_EXTENDED),
    'ProtocolTitle': ('protocolTitle', 'Protocol title', SUMMARY_EXTENDED),
    'sponsor': ('sponsor', 'Sponsor', SUMMARY_EXTENDED),
    'population': ('population', 'Study Population', SUMMARY_EXTENDED),
    'soa_footnotes': ('soa_footnotes', 'Soa Footnotes', ''),
    'molecule_device': ('moleculeDevice', 'Molecule Device', SUMMARY_EXTENDED),
    'pro_list': ('pro_list', 'Pro List', PATIENT_COMPLEXITY)
}

EXCLUDED_LM_ACCORDIANS = []

SUMMARY_TYPES = {
    'versionDate': ('date', '%Y%m%d'),
    'approvalDate': ('date', '%Y%m%d'),
    'uploadDate': ('date', '%Y%m%d%H%M%S')
}

SUMMARY_FIELDS = {"Protocol Name": "fileName",
                  "Protocol Number": "protocol",
                  "Protocol title": "protocolTitle",
                  "Protocol Title Short": "shortTitle",
                  "Is Amendment": "isAmendment",
                  "Amendment Number": "amendment",
                  "Trial Phase": "phase",
                  "Sponsor": "sponsor",
                  "Sponsor Address": "sponsorAddress",
                  "Drug": "drug",
                  "Approval Date": "approvalDate",
                  "Version Number": "versionNumber",
                  "Version Date": "versionDate",
                  "Blinded": "blinded",
                  "Compound Number": "compoundNumber",
                  "Control": "control",
                  "Investigator": "investigator",
                  "Study Id": "studyId",
                  "Number of Subjects": "numOfSubjects",
                  "Participant Age": "participantAge",
                  "Participant Sex": "participantSex",
                  "Trial Type randomized": "trialTypeRandomized",
                  "Molecule Device": "moleculeDevice",
                  "Document Status": "documentStatus",
                  "Indication": "indication",
                  "Study Population": "population"
                  }
SUMMARY_ATTR_REV_MAP = {v: k for k, v in SUMMARY_FIELDS.items()}


class _GeneralConfig:
    summary_std_tags = _SummaryConfig.summary_std_tags

    soa_std_tags = {
        'KEY_HeaderCellIndex': 'IsHeaderCell',
        'KEY_TableIndex': 'TableIndex',
        'KEY_RowIndex': 'RowIndex',
        'KEY_ColIndex': 'ColIndex',
        'KEY_IsFootnote': 'IsFootNote',
        'KEY_FootNoteLink': 'FootNoteLink',
        'KEY_TableName': 'TableName',
        'KEY_FullText': 'FullText'
    }

    toc_std_tags = {'KEY_Toc': 'IsToc',
                    'KEY_TableOfTable': 'IsTableOfTable',
                    'KEY_TableOfFigure': 'IsTableOfFigure',
                    'KEY_TableOfAppendix': 'IsTableOfAppendix',
                    }

    other_std_tags = {'KEY_SectionHeaderPrintPage': 'SectionHeaderPrintPage',
                      'KEY_IsSectionHeader': 'IsSectionHeader',
                      'KEY_Default': '',
                      }

    cpt_std_tags = {
        'KEY_std_section_hdr': 'standard_template_placeholder',
        'KEY_std_section_hdr_level': 'standard_template_level',
        'KEY_std_section_hdr_prefix': 'standard_template_prefix',
        'KEY_std_section_element': 'standard_template_placeholder_item',
        'KEY_std_section_element_level': 'standard_template_level_item',
        'KEY_std_section_element_prefix': 'standard_template_prefix_item',
    }

    es_metadata_mapping = {
        "ProtocolTitle": "protocol_title",
        "ShortTitle": "protocol_title_short",
        "AmendmentNumber": "amendment_number",
        "IsAmendment": "is_amendment",
        "phase": "trial_phase",
        "SponsorName": "sponsor",
        "SponsorAddress": "sponsor_address",
        "Drug": "drug",
        "approval_date": "approval_date",
        "VersionNumber": "version_number",
        "VersionDate": "version_date",
        "Blinding": "blinded",
        "Compound": "compound_number",
        "Control": "control",
        "Investigator": "investigator",
        "StudyId": "study_id",
        "numOfSubjects": "number_of_subjects",
        "ParticipantAge": "participant_age",
        "ParticipantSex": "participant_sex",
        "ExclusionSection": "exclusion_criteria",
        "InclusionSection": "inclusion_criteria",
        "Indication": "indication",
        "ObjectivesSection": "objectives_section",
        "Population": "study_population",
        "EntitiesInAssessments": "entities_in_assessments",
        "SoaEpochs": "soa_epochs",
        "SoaFootnote": "assessment_footnote",
        "uploadDate": "upload_date",
        "ProtocolNo": "protocol_number",
        "StudyStatus": "study_status",
        "MoleculeDevice": "molecule_device",
        "secondary_objectives": "secondary_objectives",
        "protocol_name": "protocol_name",
        "endpoints": "endpoints",
        "trial_type_randomized": "trial_type_randomized"
    }

    UNMAPPED_SECTION_NAME = 'Unmapped'
    INIT_FILE_SECTION_NAME = 'TITLE'
    GOOD_FILE_SECTION_COUNT_MIN = 10

    TABLE_INDEX_KEY = 'KEY_TableIndex'
    TABLE_NAME_KEY = 'KEY_TableName'
    FOOTNOTE_KEY = 'KEY_IsFootNote'
    DEFAULT_KEY = ('KEY_Default', '')

    std_tags_dict = defaultdict(lambda: _GeneralConfig.DEFAULT_KEY[1],
                                {**summary_std_tags, **soa_std_tags, **toc_std_tags, **other_std_tags})

    empty_df = pd.DataFrame()
    dict_orient_type = "split"
    empty_json = json.dumps(empty_df.to_dict(orient=dict_orient_type))

    SEARCH_ROLLUP_COLUMN = 'CPT_section'  # 'level_1_CPT_section'

    # Redaction
    REDACTION_SUBCATEGORY_KEY = 'RedactionSubcategory'
    REGEX_SPECIAL_CHAR_REPLACE = re.compile('([^a-zA-Z0-9])')


class ModuleConfig:
    """Main module config."""
    GENERAL = _GeneralConfig()
    SUMMARY = _SummaryConfig()


EVENT_CONFIG = {"QC_COMPLETED": {
    "qc_complete": True}, "EDITED": {"edited": True}, "NEW_DOCUMENT_VERSION": {"new_document_version": True}}


EDITED_EVENT_TEST_CASE_PROTOCOL = 'Test_Assessment'

LAST_PROTOCOL_ACCESS = 10

XML_SUFFIX = "*.xml*"

DIGITIZER_USER_NOTIFICATION_MESSAGES = {
    "DIGITIZER1_STARTED": 'Digitization In Progress',
    "DIGITIZER2_STARTED": 'Digitization In Progress',
    "DIGITIZER1_COMPLETED": 'Digitization In Progress',
    "DIGITIZER2_COMPLETED": 'Digitization In Progress',
    "DIGITIZER2_OMOPUPDATE_STARTED": 'Digitization In Progress',
    "DIGITIZER2_OMOPUPDATE_COMPLETED": 'Digitization In Progress',
    "I2E_OMOP_UPDATE_STARTED": 'Digitization In Progress',
    "I2E_OMOP_UPDATE_COMPLETED": 'Digitization In Progress',
    "TRIAGE_STARTED": 'Upload Complete',
    "TRIAGE_COMPLETED": 'Upload Complete',
    "EXTRACTION_STARTED": 'Extraction In Progress',
    "EXTRACTION_COMPLETED": 'Extraction In Progress',
    "FINALIZATION_STARTED": 'Extraction In Progress',
    "FINALIZATION_COMPLETED": 'Extraction In Progress',
    "PROCESS_COMPLETED": 'Digitization Complete',
    "ERROR": 'Digitization Error',
    "COMPARISON_STARTED": 'Comparison In Progress',
    "COMPARISON_COMPLETED": 'Comparison In Progress',
    "QC1": 'QC Review',
    "QC2": 'QC Review'
}

QC_USER_NOTIFICATION_MESSAGES = {
    "QC_NOT_STARTED": 'QC Not Started',
    "QC1": 'QC In Progress',
    "QC2": 'QC In Progress',
    "FEEDBACK_RUN": 'QC In Progress',
    "QC_COMPLETED": 'QC Completed',
}

TABLE_DATA_TYPE = 'table'