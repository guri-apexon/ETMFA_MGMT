import glob
import logging
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from etmfa_core.aidoc.io import IQVDocument, read_iqv_xml

from etmfa.consts import Consts as consts
from etmfa.server import config
from etmfa.server.config import ModuleConfig

logger = logging.getLogger(consts.LOGGING_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

class SummaryResponse:
    def __init__(self, id: str, response_type:str = "split", table_response_type:str = "json"):
        self.id = id
        self.iqv_document = self.get_iqv_document_from_aidocid()
        self.response_type = response_type
        self.table_response_type = table_response_type

    def get_table_contents(self, table_indexes) -> dict:
        """
        Provides table contents in the requested format for all the table_indexes
        """
        table_details = dict()
        table_df = pd.DataFrame()
        logger.info(f"Extracting table contents for: {self.iqv_document} and {table_indexes}")

        if len(table_indexes) == 0:
            return table_details

        interested_properties = list(ModuleConfig.GENERAL.std_tags_dict.values()) 
        table_index_tag = ModuleConfig.GENERAL.std_tags_dict[ModuleConfig.GENERAL.TABLE_INDEX_KEY]

        for table in self.iqv_document.DocumentTables:
            if any([True if (prop.key == table_index_tag and str(prop.value) in table_indexes) else False for prop in table.Properties]):
                for row in table.ChildBoxes:                           
                    for column in row.ChildBoxes:
                        for textblock in column.ChildBoxes:
                            dict_table=dict()
                            df_list=[]
                            col_values = []
                            for prop in textblock.Properties:                            
                                if (prop.key!='ColIndex' and  prop.key in interested_properties):
                                    dict_table[prop.key]=prop.value
                                elif prop.key=='ColIndex':
                                    col_values=prop.value[1:-1].split(',')                        
                            for col in col_values:
                                dict_table_col = dict_table.copy()
                                dict_table_col ['ColIndex']=col.strip()
                                df_list.append(dict_table_col) 

                            table_df=table_df.append(pd.DataFrame(df_list))

        if table_df.shape[0] == 0:
            return table_details

        table_df[['TableIndex','RowIndex','ColIndex']] = table_df[['TableIndex','RowIndex','ColIndex']].astype(float)
        table_df = table_df.sort_values(['TableIndex','RowIndex','ColIndex','IsHeaderCell']).groupby(['TableIndex','RowIndex','ColIndex'])['TableIndex','FullText','ColIndex','RowIndex'].last()

        for table_index in table_indexes:    
            result_table = table_df.loc[table_df.TableIndex == float(table_index), ['RowIndex', 'ColIndex', 'FullText']].pivot(index='RowIndex',columns='ColIndex',values='FullText')
            if self.table_response_type == 'json':
                table_details[table_index] = result_table.to_json()
            if self.table_response_type == 'dataframe':
                table_details[table_index] = result_table

        return table_details

    def read_summary_tags(self) -> list:
        """
        Reads summary tags from IQVDocument object and returns it

        Input: IQVDocument object
        Output: List of summary details
        """
    
        std_summary_element_tag = ModuleConfig.GENERAL.std_tags_dict['KEY_IsSummaryElement']
        table_index_tag = ModuleConfig.GENERAL.std_tags_dict[ModuleConfig.GENERAL.TABLE_INDEX_KEY]
        footnote_tag = ModuleConfig.GENERAL.std_tags_dict[ModuleConfig.GENERAL.FOOTNOTE_KEY]
        subsection_tags = ModuleConfig.SUMMARY.subsection_tags

        all_summary_list = []
        
        for master_roi in self.iqv_document.DocumentParagraphs:
            master_roi_dict = dict()
            for kv_obj in master_roi.Properties:
                master_roi_dict[kv_obj.key] = kv_obj.value

            all_roi_tags = master_roi_dict.keys()
            # Display footnotes till table-json has footnote details
            if std_summary_element_tag not in all_roi_tags: # or footnote_tag in all_roi_tags:
                continue
                
            master_dict = dict() 
            master_font_style = master_roi_dict.get('font_style', '')
            master_dict['para_master_roi_id'] = master_roi.id

            master_dict['table_index'] = master_roi_dict.get(table_index_tag, '')
            master_dict['subsection'] = [name for name in master_roi_dict.keys() if name in subsection_tags]

            all_child_list = []
            for level_roi in master_roi.ChildBoxes:
                master_dict['para_child_roi_id'] = level_roi.id
                master_dict['para_child_roi_text'] = ' '.join(level_roi.strTexts)
                master_dict['para_child_font_details'] = {'IsBold': level_roi.fontInfo.Bold, 'font_size': level_roi.fontInfo.Size}

                for iqv_subtext in level_roi.IQVSubTextList:
                    iqv_subtext_dict=dict()
                    iqv_subtext_dict['para_subtext_roi_id'] = iqv_subtext.id
                    iqv_subtext_dict['para_subtext_text'] = iqv_subtext.strText
                    iqv_subtext_dict['para_subtext_font_details'] = {'IsBold': iqv_subtext.fontInfo.Bold, 'font_size': iqv_subtext.fontInfo.Size, 
                                                                    'font_style': master_font_style}
                    
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


    def get_summary_api_response(self) -> (dict, pd.DataFrame):
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
            if self.iqv_document is None:
                return None, None

            summary_details = self.read_summary_tags()
            raw_summary_df = pd.DataFrame(summary_details)

            len_summary_details = len(summary_details)
            if len_summary_details == 0:
                logger.warning(f"No summary section tags are present: {len_summary_details}")
                return None, None

            raw_summary_df.fillna(value='', inplace=True)
            raw_summary_df['table_index'] = raw_summary_df['table_index'].astype(str)

            # Keep single table
            raw_summary_df = raw_summary_df.loc[(raw_summary_df['table_index'] == '') | (~raw_summary_df.duplicated(subset=['table_index'], keep='first')) , :]
            raw_summary_df.reset_index(drop=True, inplace=True)                
            
            unique_table_index = [table_index for table_index in set(raw_summary_df['table_index']) if len(table_index) > 0]

            # Populate table contents
            table_index_dict = self.get_table_contents(unique_table_index)
            raw_summary_df['table_content'] = raw_summary_df['table_index'].apply(lambda col: table_index_dict.get(col, ''))
            raw_summary_df['type'] = np.where(raw_summary_df['table_index'] == '', 'text', 'table')

            summary_df = pd.DataFrame()
            summary_df['content'] = np.where(raw_summary_df['type'] == 'text', raw_summary_df['para_subtext_text'], raw_summary_df['table_content'])
            summary_df['type'] = raw_summary_df['type'] 
            summary_df['subsection'] = raw_summary_df['subsection'] 
            summary_df['font_info'] = raw_summary_df['para_subtext_font_details']

            # Remove merged table references
            summary_display_eligibile = summary_df['content'].apply(lambda x: x != '{}')
            summary_df = summary_df.loc[summary_display_eligibile, :]
            
            # Build in requested format
            summary_dict = summary_df.to_dict(orient=self.response_type)
            summary_dict['id'] = self.id
            logger.info(f"Summary section request: Response returned. # of rows: {summary_df.shape[0]}")
        except Exception as exc:
            logger.exception(f"Exception received in summary section API response:{exc}")
            return None, None
        
        return summary_dict, summary_df

    def get_iqv_document_from_aidocid(self) -> IQVDocument:
        """
        Creates IQVDocument object from the unique id of the document

        Input: Unique aidoc id of the document
        Ouput: IQVDocument object
        """
        xml_folder = str(Path(config.Config.DFS_UPLOAD_FOLDER).joinpath(self.id))
        logger.info(f"Searching in location: {xml_folder}")

        file_format = f"/{ModuleConfig.GENERAL.finalized_doc_prefix}*.xml*"

        processed_files = glob.glob(xml_folder + file_format)
        if len(processed_files):
            digitized_xml = processed_files[0]
            logger.info(f"Reading the finalized xml: {digitized_xml}")
            iqv_document = read_iqv_xml(digitized_xml)
            return iqv_document
        else:
            logger.error(f"Could not locate the final processed file in folder: {xml_folder}")
            return None
