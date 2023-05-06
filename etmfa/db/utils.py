import logging
import os
from datetime import datetime
from typing import Tuple

import pandas as pd

from etmfa.consts import Consts as consts
from etmfa.db import config
from etmfa.db.models.pd_protocol_qc_summary_data import PDProtocolQCSummaryData
from etmfa.server.namespaces.serializers import latest_protocol_contract_fields
from typing import Tuple

logger = logging.getLogger(consts.LOGGING_NAME)
os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"


def clean_inputs(protocol_number="", version_number="", approval_date="", aidoc_id="", document_status="", qc_status="",
                 compare_doc_id="", upload_date="", start_date="", end_date="", version_date="") -> dict:
    """
    Clean the input arguments
    """
    cleaned_inputs = dict()

    # Clean the inputs
    cleaned_inputs['protocol_number'] = protocol_number.strip(
    ) if protocol_number is not None else ''
    cleaned_inputs['version_number'] = version_number.strip(
    ) if version_number is not None else ''
    cleaned_inputs['approval_date'] = approval_date.strip(
    ) if approval_date is not None else ''
    cleaned_inputs['aidoc_id'] = aidoc_id.strip(
    ) if aidoc_id is not None else ''
    cleaned_inputs['document_status'] = document_status.strip(
    ).lower() if document_status is not None else ''
    cleaned_inputs['qc_status'] = qc_status.strip(
    ).lower() if qc_status is not None else ''
    cleaned_inputs['compare_doc_id'] = compare_doc_id.strip(
    ) if compare_doc_id is not None else ''
    cleaned_inputs['version_date'] = version_date.strip(
    ) if version_date is not None else ''
    cleaned_inputs['upload_date'] = upload_date.strip(
    ) if upload_date is not None else ''
    cleaned_inputs['start_date'] = start_date.strip(
    ) if start_date is not None else ''
    cleaned_inputs['end_date'] = end_date.strip(
    ) if end_date is not None else ''

    return cleaned_inputs


def validate_inputs(protocol_number="") -> bool:
    """
    Verify if the input arguments are valid to proceed further OR not
    """
    cleaned_inputs = clean_inputs(protocol_number=protocol_number)
    protocol_number = cleaned_inputs.get('protocol_number', '')

    if protocol_number:
        return True
    else:
        return False


def get_filter_conditions(protocol_number, version_number="", approval_date="", id="", document_status="") -> Tuple[(str, str)]:
    """
    Build dynamic filter condition based on input arguments
    """
    cleaned_inputs = clean_inputs(protocol_number=protocol_number, version_number=version_number,
                                  approval_date=approval_date, aidoc_id=id, document_status=document_status)
    protocol_number = cleaned_inputs.get('protocol_number', '')
    version_number = cleaned_inputs.get('version_number', '')
    approval_date = cleaned_inputs.get('approval_date', '')
    aidoc_id = cleaned_inputs.get('id', '')
    document_status = cleaned_inputs.get('document_status', '')

    # Init
    additional_filter = None
    all_filter = None
    order_condition = None

    # Default filter
    default_filter = f"pd_protocol_metadata.\"isActive\" = True AND pd_protocol_metadata.\"protocol\" = '{protocol_number}' AND pd_protocol_metadata.source = 'QC' AND pd_protocol_metadata.\"qcStatus\" = 'QC_COMPLETED'"

    # Build filter based on document Status
    if document_status == 'all':
        all_filter = default_filter
    else:
        document_status = document_status if document_status in config.VALID_DOCUMENT_STATUS else \
            config.DEFAULT_DOCUMENT_STATUS
        document_status_filter = f"pd_protocol_metadata.\"documentStatus\" = '{document_status}'"
        all_filter = default_filter + ' AND ' + document_status_filter

    logger.debug(f"Initial all_filter: {all_filter}\n")

    # Build filter based on other input arguments
    if aidoc_id:
        logger.debug("In id type ...")
        additional_filter = f"pd_protocol_metadata.id = '{id}'"
    elif version_number and approval_date:
        logger.debug("In version_number and approval_date type ...")
        additional_filter = f"pd_protocol_metadata.\"versionNumber\" = '{version_number}' AND pd_protocol_metadata.\"approvalDate\"::date ='{approval_date}'"
    elif version_number:
        logger.debug("In version_number type ...")
        additional_filter = f"pd_protocol_metadata.\"versionNumber\" = '{version_number}'"
    elif approval_date:
        logger.debug("In approval_date type ...")
        additional_filter = f" pd_protocol_metadata.\"approvalDate\"::date = '{approval_date}'"
    else:
        logger.debug("In only protocol_number type ...")

    if additional_filter:
        all_filter = all_filter + ' AND ' + additional_filter

    # order condition
    order_condition = "pd_protocol_metadata.\"approvalDate\" desc, pd_protocol_metadata.\"uploadDate\" desc"

    logger.debug(
        f"Input arguments: protocol={protocol_number}; version_number={version_number}; approval_date={approval_date}; aidoc_id={aidoc_id}; document_status={document_status}; Dynamic conditions: {all_filter}\n order by {order_condition}")
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
    metadata_dict['source'] = field_values[7]
    metadata_dict['draftVersion'] = field_values[8]
    metadata_dict['shortTitle'] = field_values[9]
    metadata_dict['phase'] = field_values[10]
    metadata_dict['indication'] = field_values[11]
    metadata_dict['id'] = field_values[12]
    metadata_dict['blinded'] = ''
    return metadata_dict


def apply_contract_rules(top_resource: dict, metadata_fields: list, ignore_filepath=False) -> dict:
    """
    Restrict only the fields present in the contract
    """
    indication = []
    approval_date = ''
    metadata_dict = get_metadata_dict(metadata_fields)
    top_resource.update(metadata_dict)
    top_resource['amendmentFlag'] = metadata_dict['amendmentFlag'] if pd.isnull(top_resource['amendment']) else \
        top_resource['amendment']

    approval_date = approval_date if pd.isnull(top_resource['approvalDate']) else top_resource['approvalDate'].strftime(
        '%Y%m%d')
    top_resource['approvalDate'] = '' if approval_date == config.DEFAULT_DATE_VALUE else approval_date

    _ = indication if pd.isnull(top_resource['indication']) else indication.append(
        top_resource['indication'])

    top_resource['indication'] = str(indication)

    top_resource['uploadDate'] = '' if pd.isnull(
        top_resource['uploadDate']) else top_resource['uploadDate'].isoformat()
    restricted_top_resource = {key: ('' if value is None else value) for key, value in top_resource.items() if
                               key in latest_protocol_contract_fields}
    if not ignore_filepath:  # Used in download API
        restricted_top_resource['documentFilePath'] = metadata_dict['documentFilePath']
    return restricted_top_resource


def post_process_resource(resources, multiple_records=False) -> dict:
    """
    Align the resources based on the API contract
    """
    top_resource = None

    if multiple_records and resources is not None and type(resources) == list and len(resources) > 0:
        resource_list = []
        logger.debug("\nALL_RESPONSE:")
        for idx, resource in enumerate(resources):
            logger.debug(f"\n----- Processing for {idx} resource...")
            resource_dict = resource[0].as_dict()
            resource_dict = apply_contract_rules(top_resource=resource_dict, metadata_fields=resource[1:],
                                                 ignore_filepath=True)
            resource_list.append(resource_dict)

        first_row = resources[0]
        top_resource = first_row[0].as_dict()

        top_resource = apply_contract_rules(top_resource=top_resource, metadata_fields=first_row[1:],
                                            ignore_filepath=True)
        top_resource['allVersions'] = resource_list

    elif not multiple_records and resources is not None:
        logger.debug("\nTOP_1_RESPONSE:")
        top_resource = resources[0].as_dict()

        top_resource = apply_contract_rules(top_resource=top_resource, metadata_fields=resources[1:],
                                            ignore_filepath=False)
    else:
        logger.warning("No data for post process")

    logger.debug(f"top_resource:\n{top_resource}")
    return top_resource


def filter_qc_status(resources, qc_status):
    """
        Filter the results based on qc_status
    """
    qc_status = qc_status if qc_status in config.VALID_QC_STATUS else config.DEFAULT_QC_STATUS

    if resources is not None and type(resources) == list and len(resources) > 0:
        if qc_status == config.DEFAULT_QC_STATUS:
            resources = [
                resource for resource in resources if resource.source == 'QC']
        else:
            resources = [
                resource for resource in resources if resource.rank == 1]

    return resources


def all_filters(version_date="", approval_date="", start_date="", end_date="", document_status="", upload_date="",
                qc_status="") -> tuple:
    """
    Build dynamic filter condition based on input arguments
    """
    cleaned_inputs = clean_inputs(upload_date=upload_date, version_date=version_date, approval_date=approval_date,
                                  start_date=start_date, end_date=end_date, document_status=document_status,
                                  qc_status=qc_status)
    start_date = cleaned_inputs.get('start_date', '')
    end_date = cleaned_inputs.get('end_date', '')
    approval_date = cleaned_inputs.get('approval_date', '')
    upload_date = cleaned_inputs.get('upload_date', '')
    version_date = cleaned_inputs.get('version_date', '')
    document_status = cleaned_inputs.get('document_status', '')
    qc_status = cleaned_inputs.get('qc_status', '')

    all_filters = "pd_protocol_metadata.\"isActive\" = True "

    if document_status:
        logger.debug("Documents status ...")
        all_filters += f" AND pd_protocol_metadata.\"documentStatus\" = '{document_status}'"
    if version_date:
        logger.debug("In version_date type ...")
        all_filters += f" AND pd_protocol_metadata.\"versionDate\" = '{version_date}'"
    if approval_date:
        logger.debug("In approval_date type ...")
        all_filters += f"AND pd_protocol_metadata.\"approvalDate\"::date = '{approval_date}'"
    if upload_date:
        logger.debug("In upload_date type ...")
        all_filters += f" AND pd_protocol_metadata.\"uploadDate\"::date = '{upload_date}'"
    if start_date and end_date:
        logger.debug("In start_date and end_date type ...")
        all_filters += f" AND pd_protocol_metadata.\"timeCreated\" BETWEEN '{start_date}' and '{end_date}' "
    if qc_status:
        logger.debug("In qc_status type ...")
        all_filters += f" AND pd_protocol_metadata.\"qcStatus\" = '{qc_status.upper()}'"

    logger.debug(f"top_resource:\n{all_filters}")

    return all_filters
