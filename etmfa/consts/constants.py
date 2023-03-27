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

ACCORDIAN_DOC_ID = '1'*10
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

LEGACY_QUEUE_NAMES=['triage','digitizer1','digitizer2','i2e_omop_update','digitizer2_omopupdate','extraction']

@unique
class QcStatus(Enum):
    """PD Quality Check status"""
    NOT_STARTED = 'QC_NOT_STARTED'
    QC1 = 'QC1'
    QC2 = 'QC2'
    COMPLETED = 'QC_COMPLETED'


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
                'KEY_TableIndex': 'TableIndex'}

    subsection_tags = [value for key,value in summary_std_tags.items() if key not in ('KEY_IsSummaryHeader', 'KEY_IsSummaryElement', 'KEY_TableIndex')]

    summary_key_list = {
        "protocol_name":"Protocol Name", "protocol_number":"Protocol Number", "protocol_title":"Protocol Title",
        "protocol_title_short":"Protocol Title Short", "is_amendment":"Is Amendment", "amendment_number":"Amendment Number",
        "trial_phase":"Trial Phase", "sponsor":"Sponsor", "sponsor_address":"Sponsor Address", "drug":"Drug",
        "approval_date":"Approval Date", "version_number":"Version Number", "version_date":"Version Date",
        "blinded":"Blinded", "compound_number":"Compound Number", "control":"Control", "investigator":"Investigator",
        "study_id":"Study Id", "number_of_subjects":"Number Of Subjects", "participant_age":"Participant Age",
        "participant_sex":"Participant Sex", "exclusion_criteria":"Exclusion Criteria",
        "inclusion_criteria":"Inclusion Criteria", "indication":"Indication", "primary_objectives":"Primary Objectives",
        "secondary_objectives":"Secondary Objectives", "study_status":"Study Status",
        "study_population":"Study Population", "endpoints":"Endpoints", "trial_type_randomized":"Trial Type Randomized",
        "molecule_device":"Molecule Device"
    }


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

    cpt_std_tags = {
                'KEY_std_section_hdr': 'standard_template_placeholder',
                'KEY_std_section_hdr_level' : 'standard_template_level',
                'KEY_std_section_hdr_prefix': 'standard_template_prefix',
                'KEY_std_section_element': 'standard_template_placeholder_item',
                'KEY_std_section_element_level' : 'standard_template_level_item',
                'KEY_std_section_element_prefix': 'standard_template_prefix_item',
                }

    es_metadata_mapping = {
        "ProtocolTitle": "protocol_title",
        "ShortTitle": "protocol_title_short",
        "AmendmentNumber": "amendment_number",
        "IsAmendment":"is_amendment",
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
        "NumberOfSubjects": "number_of_subjects",
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

    std_tags_dict = defaultdict(lambda: _GeneralConfig.DEFAULT_KEY[1], {**summary_std_tags, **soa_std_tags, **toc_std_tags, **other_std_tags})

    empty_df = pd.DataFrame()
    dict_orient_type = "split"
    empty_json = json.dumps(empty_df.to_dict(orient=dict_orient_type))

    SEARCH_ROLLUP_COLUMN = 'CPT_section' #'level_1_CPT_section'

    # Redaction
    REDACTION_SUBCATEGORY_KEY = 'RedactionSubcategory'
    REGEX_SPECIAL_CHAR_REPLACE = re.compile('([^a-zA-Z0-9])')





class ModuleConfig:
    """Main module config."""
    GENERAL = _GeneralConfig()
    SUMMARY = _SummaryConfig()