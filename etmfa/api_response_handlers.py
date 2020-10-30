from etmfa.server import config
from etmfa_core.aidoc.io import IQVDocument, read_iqv_xml
from collections import Counter

import glob
import logging
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from pathlib import Path

from etmfa.consts import Consts as consts
logger = logging.getLogger(consts.LOGGING_NAME)


def read_summary_tags(iqv_document: IQVDocument) -> list:
    """
    Reads summary tags from IQVDocument object and returns it

    Input: IQVDocument object
    Output: List of summary details
    """
  
    std_summary_element_tag = config.std_tags_dict['KEY_IsSummaryElement']
    std_summary_table_tag = config.std_tags_dict['KEY_TableROI']

    all_summary_list = []
    
    for master_roi in iqv_document.DocumentParagraphs:
        master_roi_dict = dict()
        for kv_obj in master_roi.Properties:
            master_roi_dict[kv_obj.key] = kv_obj.value
        
        if std_summary_element_tag not in master_roi_dict.keys():
            continue
            
        master_dict = dict() #{'para_master_roi_id': '', 'table_roi_id': ''}
        master_font_style = master_roi_dict.get('font_style', '')
        master_dict['para_master_roi_id'] = master_roi.id
        master_dict['table_roi_id'] = master_roi_dict.get(std_summary_table_tag, '')
        all_child_list = []
        for level_roi in master_roi.ChildBoxes:
            master_dict['para_child_roi_id'] = level_roi.id
            master_dict['para_child_roi_text'] = ' '.join(level_roi.strTexts)
            master_dict['para_child_font_details'] = {'IsBold': level_roi.fontInfo.Bold, 'font_size': level_roi.fontInfo.Size}

            for iqv_subtext in level_roi.IQVSubTextList:
                iqv_subtext_dict=dict()
                iqv_subtext_dict['para_subtext_roi_id'] = iqv_subtext.id
                iqv_subtext_dict['para_subtext_text'] = iqv_subtext.strText
                iqv_subtext_dict['para_subtext_font_details'] = {'IsBold': iqv_subtext.fontInfo.Bold, 'font_size': iqv_subtext.fontInfo.Size, 'font_style': master_font_style}
                
                iqv_subtext_dict.update(master_dict)
                all_child_list.append(iqv_subtext_dict)
        
        if master_font_style and all_child_list:
            combined_text = ''
            for detail in all_child_list:
                combined_text += ' ' + detail['para_subtext_text'] 
            combined_dict = all_child_list[0]
            combined_dict['para_subtext_text'] = combined_text
            all_summary_list.append(combined_dict)
        else:
            all_summary_list.extend(all_child_list)

    return all_summary_list


def get_summary_api_response(id: str, orient_type="split") -> (dict, pd.DataFrame):
    """
    Input arguments: 
    id: Unique ID of the document
    
    Returns:
    In DICT format for the summary section, contains three main sections:
        * Content: Actual text (or) table json
        * type: text or table
        * font_info: dictionary of font details
    """
    try:
        iqv_document = get_iqv_document_from_aidocid(id)

        if iqv_document is None:
            return None, None

        summary_details = read_summary_tags(iqv_document)
        raw_summary_df = pd.DataFrame(summary_details)

        len_summary_details = len(summary_details)
        if len_summary_details == 0:
            logger.warning(f"No summary section tags are present: {len_summary_details}")
            return None, None
        
        #TODO: Sprint2 - Enrich with table json details for each table_roi_id
        
        summary_df = pd.DataFrame()
        summary_df['content'] = np.where(raw_summary_df['table_roi_id'].apply(lambda x: len(x)) == 0, raw_summary_df['para_subtext_text'], "<Expect table JSON here>. TableId: " + raw_summary_df['table_roi_id'])
        summary_df['type'] = raw_summary_df['table_roi_id'].apply(lambda x: 'table' if len(x)> 0 else 'text')
        summary_df['font_info'] = raw_summary_df['para_subtext_font_details']
        
        # Build in requested format
        summary_dict = summary_df.to_dict(orient=orient_type)
        logger.info(f"Summary section request: Response returned. # of rows: {summary_df.shape[0]}")
    except Exception as exc:
        logger.exception(f"Exception received in summary section API response:{exc}")
        return None, None
    
    return summary_dict, summary_df


def get_iqv_document_from_aidocid(id: str) -> IQVDocument:
    """
    Creates IQVDocument object from the unique id of the document

    Input: Unique aidoc id of the document
    Ouput: IQVDocument object
    """
    xml_folder = str(Path(config.Config.DFS_UPLOAD_FOLDER).joinpath(id))
    logger.info(f"Searching in location: {xml_folder}")

    file_format = f"/{config.finalized_doc_prefix}*.xml*"

    # processed_files = glob.glob(xml_folder + "/SE_*.xml.*")
    processed_files = glob.glob(xml_folder + file_format)
    if len(processed_files):
        digitized_xml = processed_files[0]
        logger.info(f"Going to process for {digitized_xml}")
        iqv_document = read_iqv_xml(digitized_xml)
        return iqv_document
    else:
        logger.error(f"Could not locate the final processed file in folder: {xml_folder}")
        return None

