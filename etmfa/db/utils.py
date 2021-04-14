import logging
import os

import pandas as pd
from etmfa.consts import Consts as consts
from etmfa.server.namespaces.serializers import latest_protocol_contract_fields

DEFAULT_DATE_VALUE = '19000101'
logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"


def clean_inputs(protocol_number="", version_number="", approval_date="", aidoc_id="", document_status="") -> dict:
    """
    Clean the input arguments
    """
    cleaned_inputs = dict()

    # Clean the inputs
    cleaned_inputs['protocol_number'] = protocol_number.strip()
    cleaned_inputs['version_number'] = version_number.strip()
    cleaned_inputs['approval_date'] = approval_date.strip()
    cleaned_inputs['aidoc_id'] = aidoc_id.strip()
    cleaned_inputs['document_status'] = document_status.strip().lower()

    return cleaned_inputs

def validate_inputs(protocol_number = "") -> bool:
    """
    Verify if the input arguments are valid to proceed further OR not
    """
    cleaned_inputs = clean_inputs(protocol_number=protocol_number)
    protocol_number = cleaned_inputs.get('protocol_number', '')

    if protocol_number:
        return True
    else:
        return False

def get_filter_conditions(protocol_number, version_number="", approval_date="", aidoc_id="", document_status="") -> (str, str):
    """
    Build dynamic filter condition based on input arguments
    """
    cleaned_inputs = clean_inputs(protocol_number=protocol_number, version_number=version_number, approval_date=approval_date, aidoc_id=aidoc_id, document_status=document_status)
    protocol_number = cleaned_inputs.get('protocol_number', '')
    version_number = cleaned_inputs.get('version_number', '')
    approval_date = cleaned_inputs.get('approval_date', '')
    aidoc_id = cleaned_inputs.get('aidoc_id', '')
    document_status = cleaned_inputs.get('document_status', '')

    # Init
    additional_filter = None
    all_filter = None
    order_condition = None
    
    # Default filter
    default_filter = f"pd_protocol_qc_summary_data.isActive = 1 AND pd_protocol_metadata.protocol = '{protocol_number}'"
    
    # Build filter based on document Status
    if document_status == 'all':
        all_filter = default_filter
    else:
        document_status = document_status if document_status in ('final', 'draft', 'all') else 'final'
        document_status_filter = f"pd_protocol_metadata.documentStatus = '{document_status}'"
        all_filter = default_filter + ' AND ' + document_status_filter
        
    logger.debug(f"Initial all_filter: {all_filter}\n")
        
    # Build filter based on other input arguments
    if aidoc_id:
        logger.debug("In aidoc_id type ...")
        additional_filter = f"pd_protocol_metadata.id = '{aidoc_id}'"
    elif version_number and approval_date:
        logger.debug("In version_number and approval_date type ...")
        additional_filter = f"pd_protocol_qc_summary_data.versionNumber = '{version_number}' AND CONVERT(VARCHAR(8), pd_protocol_qc_summary_data.approvalDate, 112) = '{approval_date}'"
    elif version_number:
        logger.debug("In version_number type ...")
        additional_filter = f"pd_protocol_qc_summary_data.versionNumber = '{version_number}'"
    elif approval_date:
        logger.debug("In approval_date type ...")
        additional_filter = f"CONVERT(VARCHAR(8), pd_protocol_qc_summary_data.approvalDate, 112) = '{approval_date}'"
    else:
        logger.debug("In [only protocol_number] type ...")

    if additional_filter:
        all_filter = all_filter + ' AND ' + additional_filter
        
    # order condition
    order_condition = f"pd_protocol_qc_summary_data.approvalDate desc, pd_protocol_metadata.uploadDate desc"        

    logger.debug(f"Input arguments: protocol={protocol_number}; version_number={version_number}; approval_date={approval_date}; aidoc_id={aidoc_id}; document_status={document_status} \
                  \nDynamic conditions: {all_filter}\n order by {order_condition}")
    return all_filter, order_condition

def get_metadata_dict(field_values) -> dict:
    """
    Assign metadata fields into appropriate field name
    """
    metadata_dict = dict()
    metadata_dict['draftNumber'] = field_values[0]
    metadata_dict['amendmentFlag'] = field_values[1]
    metadata_dict['uploadDate'] = field_values[2]
    metadata_dict['documentFilePath'] = field_values[3]
    metadata_dict['projectId'] = field_values[4]
    metadata_dict['documentStatus'] = field_values[5]
    metadata_dict['protocol'] = field_values[6]
    return metadata_dict

def apply_contract_rules(top_resource:dict, metadata_fields:list, ignore_filepath=False) -> dict:
    """
    Restrict only the fields present in the contract
    """
    indications = []
    approval_date = ''
    metadata_dict = get_metadata_dict(metadata_fields)
    top_resource.update(metadata_dict)

    approval_date = approval_date if pd.isnull(top_resource['approvalDate']) else top_resource['approvalDate'].strftime('%Y%m%d')
    top_resource['approvalDate'] = '' if approval_date == DEFAULT_DATE_VALUE else approval_date
    
    _ = indications if pd.isnull(top_resource['indications']) else indications.append(top_resource['indications'])
    top_resource['indications'] = str(indications)
    
    top_resource['uploadDate'] = '' if pd.isnull(top_resource['uploadDate']) else top_resource['uploadDate'].isoformat()
    restricted_top_resource = {key:('' if value is None else value) for key, value in top_resource.items() if key in latest_protocol_contract_fields}

    if not ignore_filepath: # Used in download API
        restricted_top_resource['documentFilePath'] = metadata_dict['documentFilePath']
    return restricted_top_resource


def post_process_resource(resources, multiple_records=False) -> dict:
    """
    Align the resources based on the API contract
    """
    top_resource = None

    if multiple_records and resources is not None and type(resources) == list and len(resources) > 0:
        resource_list = []
        logger.debug(f"\nALL_RESPONSE:")
        for idx, resource in enumerate(resources):
            logger.debug(f"\n----- Processing for {idx} resource...")
            resource_dict = resource[0].as_dict()

            resource_dict = apply_contract_rules(top_resource = resource_dict, metadata_fields = resource[1:], ignore_filepath = True)
            resource_list.append(resource_dict)
        
        first_row = resources[0]
        top_resource = first_row[0].as_dict()

        top_resource = apply_contract_rules(top_resource = top_resource, metadata_fields = first_row[1:], ignore_filepath = True)
        top_resource['allVersions'] = resource_list
        
    elif not multiple_records and resources is not None:
        logger.debug(f"\nTOP_1_RESPONSE:")
        top_resource = resources[0].as_dict()
        
        top_resource = apply_contract_rules(top_resource = top_resource, metadata_fields = resources[1:], ignore_filepath = False)
    else:
        logger.warning(f"No data for post process")

    logger.debug(f"top_resource:\n{top_resource}")
    return top_resource
