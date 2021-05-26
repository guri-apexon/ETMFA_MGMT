# Source type
SRC_EXTRACT = 'LM'
SRC_QC = 'QC'
JSON_DEFAULT_MISSING_VALUE = ''

# Valid status
VALID_DOCUMENT_STATUS = ('final', 'draft', 'all')
DEFAULT_DOCUMENT_STATUS = 'final'

VALID_QC_STATUS = ('qc_only', 'all')
DEFAULT_QC_STATUS = 'qc_only'

DEFAULT_DATE_VALUE = '19000101'

# Mapping between table name and JSON field name
# Format: 'table_name': ('json_field_name', 'max_allowed_length', 'data_type', 'data_format')
summary_table_json_mapper = { 
    'sponsor': ('sponsor', 256, 'string', ''),
    'protocolNumber': ('protocol_number', 64, 'string', ''),
    'trialPhase': ('trial_phase', 16, 'string', ''),
    'versionNumber': ('version_number', 64, 'string', ''),
    'amendmentNumber': ('amendment_number', 64, 'string', ''),
    'approvalDate': ('approval_date', 8, 'date', '%Y%m%d'),
    'versionDate': ('version_date', 8, 'date', '%Y%m%d'),
    'protocolTitle': ('protocol_title', 1024, 'string', ''),
    'protocolShortTitle': ('protocol_title_short', 512, 'string', ''),
    'indications': ('indication', 1024, 'string', ''),
    'moleculeDevice': ('molecule_device', 128, 'string', ''),
    'investigator': ('investigator', 128, 'string', ''),
    'blinded': ('blinded', 64, 'string', ''),
    'drug': ('drug', 256, 'string', ''),
    'compoundNumber': ('compound_number', 256, 'string', ''),
    'control': ('control', 512, 'string', ''),
    'endPoints': ('endpoints', 4096, 'string', ''),
    'trialTypeRandomized': ('trial_type_randomized', 2048, 'string', ''),
    'sponsorAddress': ('sponsor_address', 512, 'string', ''),
    'numberOfSubjects': ('number_of_subjects', 32, 'string', ''),
    'participantAge': ('participant_age', 64, 'string', ''),
    'participantSex': ('participant_sex', 16, 'string', ''),
    'studyPopulation': ('study_population', 1024, 'string', ''),
    'inclusionCriteria': ('inclusion_criteria', 4096, 'string', ''),
    'exclusionCriteria': ('exclusion_criteria', 4096, 'string', ''),
    'primaryObjectives': ('primary_objectives', 4096, 'string', ''),
    'secondaryObjectives': ('secondary_objectives', 4096, 'string', ''),
    'protocolName': ('protocol_name', 256, 'string', ''),
    'isAmendment': ('is_amendment', 8, 'string', ''),
}
