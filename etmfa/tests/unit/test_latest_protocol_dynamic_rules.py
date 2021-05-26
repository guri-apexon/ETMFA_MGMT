import logging

import pandas as pd
import pytest
import pytest_check as check
from etmfa.consts import Consts as consts
from etmfa.db import utils

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)

def check_clauses(result, order_result, document_status):
    summ_table = "pd_protocol_qc_summary_data"
    metadata_table = "pd_protocol_metadata"

    # Preprocessing
    document_status = document_status if document_status in ('final', 'draft', 'all') else 'final'

    # Init
    is_active_clause_str = f"{summ_table}.isActive"
    protocol_clause_str  = f"{metadata_table}.protocol"
    doc_status_clause_str = f"{metadata_table}.documentStatus = '{document_status}'"
    aidocid_clause_str = f"{metadata_table}.id"
    version_num_clause_str = f"{summ_table}.versionNumber"
    approval_date_clause_str = f"{summ_table}.approvalDate"
    order_by_clause_str = f"{summ_table}.approvalDate desc, {metadata_table}.uploadDate desc"

    # Build clause present flags
    # Flag order: is_active, protocol_number, version_number, approval_date, aidoc_id, document_status, order_by clause
    clause_present_list = []
    clause_present_list.append(1 if is_active_clause_str in result else 0)
    clause_present_list.append(1 if protocol_clause_str in result else 0)
    clause_present_list.append(1 if version_num_clause_str in result else 0)
    clause_present_list.append(1 if approval_date_clause_str in result else 0)
    clause_present_list.append(1 if aidocid_clause_str in result else 0)
    clause_present_list.append(1 if doc_status_clause_str in result else 0)
    clause_present_list.append(1 if order_by_clause_str in order_result else 0)

    return clause_present_list


@pytest.mark.parametrize("protocol_number, version_number, approval_date, aidoc_id, document_status, input_type, expected_clauses", 
                    [("0212_D361BC00001", '1', '20210404', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', 'final', "all_inputs", [1, 1, 0, 0, 1, 1, 1]),
                    ("0212_D361BC00001", '', '', '', '', "Only protocol", [1, 1, 0, 0, 0, 1, 1]),
                    ("0212_D361BC00001", '', '', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', '', "Protocol and aidocid", [1, 1, 0, 0, 1, 1, 1]),
                    ("0212_D361BC00001", '1', '', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', '', "Version and aidocid", [1, 1, 0, 0, 1, 1, 1]),
                    ("0212_D361BC00001", '', '20210404', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', '', "approval_date and aidocid", [1, 1, 0, 0, 1, 1, 1]),
                    ("0212_D361BC00001", '1', '20210404', '017b3ecc-57a1-4fff-9d04-a0e98437dc38', '', "version, approval_date and aidocid", [1, 1, 0, 0, 1, 1, 1]),
                    ("0212_D361BC00001", '1', '', '', '', "Only version", [1, 1, 1, 0, 0, 1, 1]),
                    ("0212_D361BC00001", '', '20210404', '', '', "Only approval_date", [1, 1, 0, 1, 0, 1, 1]),
                    ("0212_D361BC00001", '1', '20210404', '', '', "Both version and approval_date", [1, 1, 1, 1, 0, 1, 1]),
                    ("0212_D361BC00001", '1', '20210404', '', 'final', "final status", [1, 1, 1, 1, 0, 1, 1]),
                    ("0212_D361BC00001", '1', '20210404', '', 'draft', "draft status", [1, 1, 1, 1, 0, 1, 1]),
                    ("0212_D361BC00001", '1', '20210404', '', 'all', "all status", [1, 1, 1, 1, 0, 0, 1]),
                    ("0212_D361BC00001", '1', '20210404', '', '', "empty status", [1, 1, 1, 1, 0, 1, 1]),
                    ])
def test_dynamic_rules(protocol_number, version_number, approval_date, aidoc_id, document_status, input_type, expected_clauses):
    all_filter, order_condition = utils.get_filter_conditions(protocol_number, version_number, approval_date, aidoc_id, document_status)
    clauses_present_flags = check_clauses(all_filter, order_condition, document_status)

    check.equal(clauses_present_flags, expected_clauses, msg=f"Input args: {input_type}")

