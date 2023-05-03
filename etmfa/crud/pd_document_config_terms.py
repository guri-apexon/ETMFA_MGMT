from datetime import timezone
import pytz
from etmfa_core.postgres_db_schema import NlpEntityDb, IqvkeyvaluesetDb
from etmfa.db.models.pd_documenttables_db import DocumenttablesDb
from etmfa.db.models.pd_iqvdocumentlink_db import IqvdocumentlinkDb
from etmfa.db.models.pd_iqvexternallink_db import IqvexternallinkDb
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import or_
from typing import Tuple
import logging
from etmfa.consts import Consts as consts
from etmfa.db.models.pd_iqvvisitrecord_db import IqvvisitrecordDb
from etmfa.consts.constants import ModuleConfig

logger = logging.getLogger(consts.LOGGING_NAME)


def get_document_terms_data(db: Session, aidoc_id: str,
                            link_id: str, config_variables: str,
                            link_dict: dict) -> list:
    """
    Collect terms values based on provided configuration values for the
    document section
    terms values
    :param db: db session
    :param aidoc_id: document id
    :param link_id: section id
    :param config_variables is string separated by ,
        :param clinical_terms -- optional
        :param time_points -- optional
        :param preferred_terms -- optional
        :param redaction_attributes -- optional
        :param references -- optional
        :param properties -- optional
    :returns: list of configurable terms values
    """

    terms_values = {}

    if config_variables is None:
        return []

    if "time_points" in config_variables:
        if link_id:
            iqv_time_point_visit_records = db.query(IqvvisitrecordDb).filter(
                IqvvisitrecordDb.doc_id == aidoc_id,
                IqvvisitrecordDb.table_roi_id == link_id).all()
        else:
            iqv_time_point_visit_records = db.query(IqvvisitrecordDb).filter(
                IqvvisitrecordDb.doc_id == aidoc_id).all()
        time_points_values = [{"id": iqvvisit_record.id,
                               "time_point": iqvvisit_record.visit_timepoint,
                               "table_roi_id": iqvvisit_record.table_roi_id} for
                              iqvvisit_record in iqv_time_point_visit_records]
        terms_values.update({'time_points': time_points_values})
        logger.info(f"time points results {time_points_values}")

    if "clinical_terms" in config_variables:
        if link_dict:
            clinical_terms = db.query(NlpEntityDb).filter(
                NlpEntityDb.doc_id == aidoc_id).filter_by(**link_dict).all()
        elif link_id:
            clinical_terms = db.query(NlpEntityDb).filter(
                NlpEntityDb.doc_id == aidoc_id,
                NlpEntityDb.link_id == link_id).all()
        else:
            clinical_terms = db.query(NlpEntityDb).filter(
                NlpEntityDb.doc_id == aidoc_id).all()

        clinical_values = [
            {"id": clinical_term.id, "ontology": clinical_term.ontology,
             "parent_id": clinical_term.parent_id,
             "entity_key": clinical_term.entity_key, "text": clinical_term.text}
            for clinical_term in clinical_terms]
        terms_values.update({'clinical_terms': clinical_values})
        logger.info(f"clinical terms results {clinical_values}")

    if "preferred_terms" in config_variables:
        if link_dict:
            all_term_data = db.query(IqvdocumentlinkDb).filter(
                IqvdocumentlinkDb.doc_id == aidoc_id).filter_by(
                **link_dict).all()
            all_term_data_from_tables = db.query(DocumenttablesDb).filter(
                DocumenttablesDb.doc_id == aidoc_id).filter_by(
                **link_dict).all()
        elif link_id:
            all_term_data = db.query(IqvdocumentlinkDb).filter(
                IqvdocumentlinkDb.doc_id == aidoc_id,
                IqvdocumentlinkDb.link_id == link_id).all()
            all_term_data_from_tables = db.query(DocumenttablesDb).filter(
                DocumenttablesDb.doc_id == aidoc_id,
                DocumenttablesDb.link_id == link_id).all()
        else:
            all_term_data = db.query(IqvdocumentlinkDb).filter(
                IqvdocumentlinkDb.doc_id == aidoc_id).all()
            all_term_data_from_tables = db.query(DocumenttablesDb).filter(
                DocumenttablesDb.doc_id == aidoc_id).all()

        preferred_values = [{"id": term_record.id,
                             "preferred_term": term_record.iqv_standard_term,
                             "parent_id": term_record.parent_id,
                             "text": term_record.LinkText} for term_record in
                            all_term_data]
        preferred_values_from_tables = [{"id": tb_term_record.id,
                                         "preferred_term": tb_term_record.iqv_standard_term,
                                         "parent_id": tb_term_record.parent_id,
                                         "text": tb_term_record.strText} for
                                        tb_term_record in
                                        all_term_data_from_tables]
        all_term_records = preferred_values + preferred_values_from_tables
        terms_values.update({'preferred_terms': all_term_records})
        logger.info(f"preferred terms results {all_term_records}")

    if "references" in config_variables:
        if link_dict:
            reference_links = db.query(IqvexternallinkDb).filter(
                IqvexternallinkDb.doc_id == aidoc_id).filter_by(
                **link_dict).all()
        elif link_id:
            reference_links = db.query(IqvexternallinkDb).filter(
                IqvexternallinkDb.doc_id == aidoc_id,
                IqvexternallinkDb.link_id == link_id).all()
        else:
            reference_links = db.query(IqvexternallinkDb).filter(
                IqvexternallinkDb.doc_id == aidoc_id).all()

        references_values = [
            {"id": reference_link.id, "source_text": reference_link.source_text,
             "link_id": reference_link.link_id,
             "destination_url": reference_link.destination_url,
             "destination_link_id": reference_link.destination_link_id,
             "destination_link_prefix": reference_link.destination_link_prefix,
             "parent_id": reference_link.parent_id,
             "destination_link_text": reference_link.destination_link_text} for
            reference_link in reference_links]
        terms_values.update({'references': references_values})
        logger.info(f"references results {references_values}")

    if "properties" in config_variables:
        if link_dict:
            property_data = db.query(IqvkeyvaluesetDb).filter(
                IqvkeyvaluesetDb.doc_id == aidoc_id).filter_by(
                **link_dict).all()
        elif link_id:
            property_data = db.query(IqvkeyvaluesetDb).filter(
                IqvkeyvaluesetDb.doc_id == aidoc_id,
                IqvkeyvaluesetDb.link_id == link_id).all()
        else:
            property_data = db.query(IqvkeyvaluesetDb).filter(
                IqvkeyvaluesetDb.doc_id == aidoc_id).all()

        properties_values = [
            {"id": property.id, "key": property.key, "value": property.value,
             "parent_id": property.parent_id} for property in property_data]
        terms_values.update({'properties': properties_values})
        logger.info(f"properties results {properties_values}")

    if "redaction_attributes" in config_variables:
        if link_dict:
            redaction_values = db.query(IqvkeyvaluesetDb).filter(
                IqvkeyvaluesetDb.doc_id == aidoc_id, IqvkeyvaluesetDb.key ==
                ModuleConfig.GENERAL.REDACTION_SUBCATEGORY_KEY).filter_by(
                **link_dict).all()
        elif link_id:
            redaction_values = db.query(IqvkeyvaluesetDb).filter(
                IqvkeyvaluesetDb.doc_id == aidoc_id, IqvkeyvaluesetDb.key ==
                ModuleConfig.GENERAL.REDACTION_SUBCATEGORY_KEY,
                IqvkeyvaluesetDb.link_id == link_id).all()
        else:
            redaction_values = db.query(IqvkeyvaluesetDb).filter(
                IqvkeyvaluesetDb.doc_id == aidoc_id,
                IqvkeyvaluesetDb.key == ModuleConfig.GENERAL.REDACTION_SUBCATEGORY_KEY).all()

        redaction_att_values = [
            {"id": redaction_record.id, "key": redaction_record.key,
             "value": redaction_record.value,
             "parent_id": redaction_record.parent_id} for redaction_record in
            redaction_values]
        terms_values.update({'redaction_attributes': redaction_att_values})
        logger.info(f"redaction attributes results {redaction_att_values}")

    return [terms_values]


def get_section_audit_info(psdb: Session, aidoc_id: str, link_ids: list,
                           link_levels: list, doc_seq: list) -> list:
    """
    get section audit info

    :param psdb: db instance
    :param aidoc_id: document id
    :link_ids : link ids of document as section id
    :link_levels: link ids level
    :returns : dictionary of single record with specified values
    """
    response = []
    for link_level, link_id, seq in zip(link_levels, link_ids, doc_seq):
        link_level_dict = {1: IqvdocumentlinkDb.link_id,
                           2: IqvdocumentlinkDb.link_id_level2,
                           3: IqvdocumentlinkDb.link_id_level3,
                           4: IqvdocumentlinkDb.link_id_level4,
                           5: IqvdocumentlinkDb.link_id_level5,
                           6: IqvdocumentlinkDb.link_id_level6}

        obj = psdb.query(IqvdocumentlinkDb).filter(
            IqvdocumentlinkDb.doc_id == aidoc_id,
            link_level_dict[link_level] == link_id,
            IqvdocumentlinkDb.LinkLevel == link_level,
            IqvdocumentlinkDb.DocumentSequenceIndex == seq).first()

        current_timezone = obj.last_updated
        est_datetime = current_timezone.astimezone(timezone.utc)
        response.append({"last_reviewed_date": str(est_datetime).replace('+00:00',''),
                         "last_reviewed_by": obj.userId or '',
                         "total_no_review": obj.num_updates})

    return response


def get_preferred_data(db, doc_id: str = "", link_id: str = "", ) -> list:
    """
    Get preferred terms values for the enriched text as per doc and section id
    :param db: database object
    :param doc_id: document id
    :param link_id: link id of document as section id
    :returns: To collect all the preferred terms values for the enriched text
    from all over the section
    """
    config_variables = "preferred_terms"
    preferred_document_data = get_document_terms_data(db, doc_id, link_id,
                                                      config_variables, {})
    return preferred_document_data[0].get("preferred_terms",
                                          []) if preferred_document_data else []


def get_references_data(db, doc_id: str = "", link_id: str = "", ) -> list:
    """
    Get reference values for the sections as per doc and link id
    :param db: database object
    :param doc_id: document id
    :param link_id: link id of document as section id
    :returns: Fetch all the link and reference data from db for the sections
    """
    config_variables = "references"
    reference_data = get_document_terms_data(db, doc_id, link_id,
                                             config_variables, {})
    return reference_data[0].get("references", []) if reference_data else []


def link_id_link_level_based_on_section_text(psdb: Session, aidoc_id: str,
                                             section_text: str, link_id: str,
                                             link_level: str = "") -> Tuple[
    str, int, dict]:
    """
    :param psdb: db session
    :param aidoc_id: document id
    :param link_level: level of headers in toc
    :param link_id: section id
    :returns link_id and link_level based on section text contains
        and link_dict is link_levels and link ids as key and values
    """
    link_dict = {}
    if section_text:
        try:
            if section_text.replace('.', '').isnumeric():
                get_link_id = psdb.query(IqvdocumentlinkDb).filter(
                    IqvdocumentlinkDb.doc_id == aidoc_id,
                    IqvdocumentlinkDb.LinkType == 'toc',
                    IqvdocumentlinkDb.LinkPrefix == section_text).first()
            else:
                get_link_id = psdb.query(IqvdocumentlinkDb).filter(
                    IqvdocumentlinkDb.doc_id == aidoc_id,
                    IqvdocumentlinkDb.LinkType == 'toc',
                    or_(IqvdocumentlinkDb.iqv_standard_term == section_text,
                        func.lower(IqvdocumentlinkDb.LinkText).contains(
                            section_text.lower()))).first()

            if get_link_id is None:
                return "", 0, {}

            link_dict.update({"link_id": get_link_id.link_id,
                              "link_id_level2": get_link_id.link_id_level2,
                              "link_id_level3": get_link_id.link_id_level3,
                              "link_id_level4": get_link_id.link_id_level4,
                              "link_id_level5": get_link_id.link_id_level5,
                              "link_id_level6": get_link_id.link_id_level6})
            link_dict = {k: v for k, v in link_dict.items() if v}
            link_level_identify = list(link_dict.keys())
            length_of_link_level = len(link_level_identify)
            if length_of_link_level > 1:
                link_level = int(link_level_identify[-1].strip("link_id_level"))
            elif length_of_link_level == 1:
                link_level = 1
            link_id = link_dict[link_level_identify[-1]]
            return link_id, link_level, link_dict
        except Exception as e:
            logger.exception(
                f"Exception occurred during getting link id {section_text}, {str(e)}")

    return link_id, link_level, link_dict


def get_doc_protocol(psdb: Session, aidoc_id: str):
    """
    To get document protocol based on given document id
    """
    doc_protocol = psdb.query(PDProtocolMetadata).filter(
        PDProtocolMetadata.id == aidoc_id,
        PDProtocolMetadata.isActive == True).first()
    if doc_protocol:
        return doc_protocol.protocol or ''
