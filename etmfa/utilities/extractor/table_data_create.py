import json
from etmfa.consts.constants import TABLE_DATA_TYPE
from etmfa_core.aidoc.io import IQVDocument
from etmfa.utilities import data_extractor_utils as utils


def create_table_data(iqv_document: IQVDocument, table_sequence_index: int, table_heading: str,
                      master_dict: dict, entity_profile_genre: list) -> dict:
    """
    Function creates table data and footnote from documenttablesm and Attachment list DB table with
    getting data from top levels
    """
    for table in iqv_document.DocumentTables:
        table_foot_notes = []
        if table.DocumentSequenceIndex == table_sequence_index:

            master_dict['table_type'] = TABLE_DATA_TYPE
            master_dict['type'] = TABLE_DATA_TYPE
            row_data_count = 0
            table_data = []
            for row in table.ChildBoxes:
                col_data = []
                for column in row.ChildBoxes:
                    master_roi_fulltext = column.Value
                    # handling redaction of data with get entities at table level
                    len_redaction_entities, len_matched_redaction_entities, master_redaction_entities = utils.get_matched_redact_entity_roi(table)
                    if len(master_redaction_entities):
                        master_roi_fulltext = utils.redact_text(text=master_roi_fulltext,
                                                                text_redaction_entity=master_redaction_entities,
                                                                redact_profile_entities=entity_profile_genre,
                                                                redact_flg=True)
                    cell_data = {"cell_id": column.id, "value": master_roi_fulltext or column.Value, "op_type": None,
                                 "col_indx": len(col_data),"rowspan": column.BulletIndentationLevel or 0,
                                 "colspan": column.m_WORD_LAYOUTVal or 0}
                    col_data.append(cell_data)
                table_data.append({"row_indx": row_data_count, "roi_id": row.id, "op_type": None, "columns": col_data})
                row_data_count += 1
            master_dict['para_subtext_text'] = table.Value
            master_dict['table_content_from_master_roi'] = {"TableProperties": json.dumps(table_data),
                                                            "Table": table.Value,
                                                            "SectionHeaderPrintPage": "", "TableIndex": "1",
                                                            "TableName": table_heading}
            for foot_note in table.Attachments:
                footnote_val = {
                    'TableId': table.id,
                    'AttachmentIndex': foot_note.DocumentSequenceIndex,
                    'key': "",
                    'AttachmentId': foot_note.id,
                    'Text': foot_note.Value
                }
                table_foot_notes.append(footnote_val)
            master_dict['table_content_from_master_roi']['AttachmentListProperties'] = table_foot_notes
            master_dict['table_roi_id'] = table_data[0]['roi_id']
    return master_dict