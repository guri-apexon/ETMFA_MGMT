import logging
from collections import Counter
from typing import Optional, Tuple
import numpy as np
import pandas as pd
from etmfa_core.aidoc.io import IQVDocument
from etmfa.utilities import data_extractor_utils as utils
from etmfa.utilities.table_extractor import SOAResponse as soa
from etmfa.consts.constants import ModuleConfig
from etmfa.consts import Consts as consts
import base64

logger = logging.getLogger(consts.LOGGING_NAME)


class CPTExtractor:
    def __init__(self, iqv_document: IQVDocument, imgagebinaries: dict,
                 profile_details: dict, entity_profile_genre: list,
                 response_type: str = "split",
                 table_response_type: str = "html"):
        
        self.iqv_document = iqv_document
        self.imagebinaries = imgagebinaries
        self.response_type = response_type
        self.table_response_type = table_response_type
        self.table_index_tag = ModuleConfig.GENERAL.std_tags_dict[ModuleConfig.GENERAL.TABLE_INDEX_KEY]
        self.footnote_tag = ModuleConfig.GENERAL.std_tags_dict[ModuleConfig.GENERAL.FOOTNOTE_KEY]
        self.cpt_tags = list(ModuleConfig.GENERAL.cpt_std_tags.values())
        self.file_section_tags = ['IsSectionHeader', 'HeaderText', 'HeaderNumericSection', 'LinkLevel']
        self.interested_tags = self.cpt_tags + self.file_section_tags
        self.hdr_tag_name = ModuleConfig.GENERAL.cpt_std_tags['KEY_std_section_hdr']
        self.hdr_level_tag_name = ModuleConfig.GENERAL.cpt_std_tags['KEY_std_section_hdr_level']
        self.element_tag_name = ModuleConfig.GENERAL.cpt_std_tags['KEY_std_section_element']
        self.element_level_tag_name = ModuleConfig.GENERAL.cpt_std_tags['KEY_std_section_element_level']
        self.default_cpt_section = ModuleConfig.GENERAL.UNMAPPED_SECTION_NAME
        self.default_init_file_section = ModuleConfig.GENERAL.INIT_FILE_SECTION_NAME
        self.good_file_section_count_min = ModuleConfig.GENERAL.GOOD_FILE_SECTION_COUNT_MIN
        self.profile_details = profile_details
        self.entity_profile_genre = entity_profile_genre

    def read_cpt_tags(self) -> Tuple[list, int, int]:
        """
        Reads cpt tags from IQVDocument object and returns it

        Input: IQVDocument object
        Output: List of cpt details
        """
        all_cpt_list = []
        tot_master_childbox_redaction_entity = 0
        tot_matching_master_childbox_redaction_entity = 0
        for master_roi in self.iqv_document.DocumentParagraphs:

            master_roi_dict = dict()
            for kv_obj in master_roi.Properties:
                master_roi_dict[kv_obj.key] = kv_obj.value

            all_roi_tags = master_roi_dict.keys()
            master_dict = dict()
            master_font_style = master_roi_dict.get('font_style', '')
            master_dict['para_master_roi_id'] = master_roi.id
            master_dict['image_content'] = ''
            # For header identification
            master_dict['font_heading_flg'] = ('heading' in master_font_style.lower())
            # Collect tags
            master_dict['table_index'] = master_roi_dict.get(self.table_index_tag, '')
            master_dict['not_footnote_flg'] = False if self.footnote_tag in all_roi_tags else True
            interested_tag_dict = {key:value for key, value in master_roi_dict.items() if key in self.interested_tags}
            master_dict.update(interested_tag_dict)
            # Prep for paragraph redaction
            len_para_entities, para_entities = utils.get_redaction_entities(
                level_roi=master_roi)

            all_child_list = []
            for child_idx, level_roi in enumerate(master_roi.ChildBoxes):
                master_dict['para_child_roi_id'] = level_roi.id
                master_dict['para_child_roi_text'] = ' '.join(level_roi.Value)
                master_dict['para_child_font_details'] = {
                    'IsBold': level_roi.fontInfo.Bold,
                    'font_size': level_roi.fontInfo.Size,
                    **level_roi.fontInfo.__dict__}
                # Prep for subtext redaction
                len_redaction_entities, redaction_entities = utils.get_redaction_entities(level_roi=level_roi)
                # Added para level redaction entities with length
                len_redaction_entities += len_para_entities
                redaction_entities += para_entities
                tot_master_childbox_redaction_entity += len_redaction_entities
                childbox_entity_set = set(range(0, len_redaction_entities))
                subtext_matched_entity_set = set()

                tot_matching_master_childbox_redaction_entity += len(childbox_entity_set.intersection(subtext_matched_entity_set))
                # Debug report
                debug_notfound_entity = (childbox_entity_set - subtext_matched_entity_set)
                if len(debug_notfound_entity) > 0 and len(all_child_list) != 0:
                    logger.debug(f"Debug report: [{master_roi.id}] [{level_roi.id}]: Missing entity idx: {debug_notfound_entity} \
                        level_roi text: {level_roi.GetFullText()} ; redaction_entities: {redaction_entities}")

            if self.imagebinaries.get(master_roi.id):
                imagebinary_list = self.imagebinaries[master_roi.id]
                for imagebinary in imagebinary_list:
                    master_dict['image_type'] = "image"
                    image_dict = dict()
                    roi_id = {'para': master_roi.id, 'childbox': level_roi.id,
                              'subtext': ""}
                    master_dict['para_subtext_text'] = master_roi.Value
                    master_dict[
                        'image_content'] = f"data:image/{imagebinary.image_format};base64," + base64.b64encode(
                        imagebinary.img).decode(
                        'utf-8') if imagebinary.img else ""  # iqv_subtext.strText
                    image_dict['para_subtext_font_details'] = dict(
                        {'IsBold': level_roi.fontInfo.Bold,
                         'font_size': level_roi.fontInfo.Size,
                         'font_style': master_font_style, 'entity': "",
                         'roi_id': roi_id},
                        **level_roi.fontInfo.__dict__)

                    image_dict.update(master_dict)
                    all_child_list.append(image_dict)

            # Handling roi not having IQVSubTextList
            roi_id = {'para': master_roi.id, 'childbox': '', 'subtext': ''}
            if len(all_child_list) == 0:
                master_roi_fulltext = master_roi.Value

                len_redaction_entities, len_matched_redaction_entities, master_redaction_entities = utils.get_matched_redact_entity_roi(master_roi)
                tot_master_childbox_redaction_entity += len_redaction_entities
                tot_matching_master_childbox_redaction_entity += len_matched_redaction_entities

                if len(master_redaction_entities) and master_roi_fulltext != 'None':
                    master_roi_fulltext = utils.redact_text(text=master_roi_fulltext,
                                                      text_redaction_entity=master_redaction_entities,
                                                      redact_profile_entities=self.entity_profile_genre,
                                                      redact_flg=True)

                iqv_subtext_dict = dict()
                iqv_subtext_dict['para_subtext_roi_id'] = ''
                iqv_subtext_dict['para_subtext_text'] = (master_roi_fulltext if master_roi_fulltext != 'None' else '')
                iqv_subtext_dict['para_subtext_font_details'] = dict(
                    {'IsBold': False, 'font_size': -1,
                     'font_style': master_font_style,
                     'entity': master_redaction_entities, 'roi_id': roi_id},
                    **level_roi.fontInfo.__dict__)

                iqv_subtext_dict.update(master_dict)
                all_child_list.append(iqv_subtext_dict)

            if master_font_style and all_child_list:
                len_redaction_entities, len_matched_redaction_entities, master_redaction_entities = utils.get_matched_redact_entity_roi(master_roi)
                combined_dict = all_child_list[0]
                master_roi_fulltext = master_roi.Value
                if len(master_redaction_entities):
                    master_roi_fulltext = utils.redact_text(text=master_roi_fulltext,
                                                      text_redaction_entity=master_redaction_entities,
                                                      redact_profile_entities=self.entity_profile_genre,
                                                      redact_flg=True)

                combined_dict['para_subtext_text'] = master_roi_fulltext # master_roi.GetFullText() #combined_text
                combined_dict['para_subtext_font_details']['entity'] = master_redaction_entities
                combined_dict['para_subtext_font_details']['roi_id'] = roi_id
                all_cpt_list.append(combined_dict)
            else:
                all_cpt_list.extend(all_child_list)

            logger.debug(f"[{master_roi.id}] ['From: GetFullText']: {master_roi.GetFullText()}")
            logger.debug(f"[{master_roi.id}] ['From: ChildBoxes/SubTextList']: {all_child_list}\n")
        # Redaction summary
        logger.info(f"""Redaction summary: tot_master_childbox_redaction_entity: {tot_master_childbox_redaction_entity};\
            tot_matching_master_childbox_redaction_entity: {tot_matching_master_childbox_redaction_entity}""")
        return all_cpt_list, tot_master_childbox_redaction_entity, tot_matching_master_childbox_redaction_entity

    def set_child_sections(self, raw_cpt_df) -> Tuple[list, list]:
        """
        Sets up level1_cpt_section for entire child levels
        Sets up 'file_section', 'file_section_num', 'file_section_level' for entire child levels
        """
        recent_level_1_cpt_section = self.default_cpt_section
        level_1_cpt_section = []

        prev_file_section = self.default_cpt_section if raw_cpt_df['file_section'].nunique() < self.good_file_section_count_min else self.default_init_file_section
        file_section_details = [prev_file_section, '', 1]
        all_file_section_details = []

        for idx, row in raw_cpt_df.iterrows():
            if row.section_level == '1':
                recent_level_1_cpt_section = row.CPT_section

            if row.file_section != '' and row.file_section != prev_file_section:
                file_section_details = [row.file_section, row.file_section_num, row.file_section_level]
                prev_file_section = row.file_section

            logger.debug(f"{idx} --> {row.section_level} --> {row.CPT_section} --> {recent_level_1_cpt_section}")
            level_1_cpt_section.append(recent_level_1_cpt_section)
            all_file_section_details.append(file_section_details)

        return level_1_cpt_section, all_file_section_details

    def build_display_search(self, raw_cpt_df) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Builds data meant for display and search database
        """
        cpt_df = pd.DataFrame()
        cpt_df['section_level'] = np.where(raw_cpt_df[self.hdr_level_tag_name] != '', raw_cpt_df[self.hdr_level_tag_name], raw_cpt_df[self.element_level_tag_name])
        cpt_df['CPT_section'] = np.where(raw_cpt_df[self.hdr_tag_name] != '', raw_cpt_df[self.hdr_tag_name], raw_cpt_df[self.element_tag_name])
        cpt_df['type'] = raw_cpt_df['type']
        cpt_df['table_index'] = raw_cpt_df['table_index']
        cpt_df['para_text'] = raw_cpt_df['para_subtext_text']
        cpt_df['content'] = np.where(raw_cpt_df['type'] == "image",
                                     raw_cpt_df['image_content'], (np.where(
                raw_cpt_df['type'].isin(['header', 'text']),
                raw_cpt_df['para_subtext_text'], raw_cpt_df['table_content'])))
        cpt_df['font_info'] = raw_cpt_df['para_subtext_font_details']
        # Default CPT_section
        cpt_df['CPT_section'] = cpt_df['CPT_section'].apply(lambda section_name: ModuleConfig.GENERAL.UNMAPPED_SECTION_NAME if section_name == '' else section_name)
        # Setup flags
        cpt_df['keep_unique_table_flg'] = ~(cpt_df.loc[cpt_df['table_index'] > 0].duplicated(subset=['table_index'], keep='first'))
        cpt_df['keep_unique_table_flg'].fillna(value=True, inplace=True)
        cpt_df['not_footnote_flg'] = raw_cpt_df[['not_footnote_flg', 'type']].apply(lambda x: True if x['type'] == 'table' else x['not_footnote_flg'], axis=1)
        cpt_df['not_merged_table_flg'] = cpt_df['content'].apply(lambda x: x != '{}')
        # File section tags
        cpt_df['IsSectionHeader'] =	raw_cpt_df['IsSectionHeader']
        cpt_df['file_section'] =	raw_cpt_df['HeaderText']
        cpt_df['file_section_num'] = raw_cpt_df['HeaderNumericSection']
        cpt_df['file_section_level'] =	raw_cpt_df['LinkLevel']
        # Propogate level_1_cpt_section and file_section to its children levels
        file_section_columns = ['file_section', 'file_section_num', 'file_section_level']
        level1_cpt_section_list, file_section_list  = self.set_child_sections(cpt_df)
        cpt_df['level_1_CPT_section'] = level1_cpt_section_list
        cpt_df[file_section_columns] = file_section_list
        # Build display data
        display_columns = ['section_level', 'CPT_section', 'type', 'content', 'font_info', 'level_1_CPT_section']  + file_section_columns
        display_df = cpt_df.loc[(cpt_df['keep_unique_table_flg']) & (cpt_df['not_footnote_flg']) & (cpt_df['not_merged_table_flg']), display_columns]
        display_df['seq_num'] = range(1, display_df.shape[0]+1)
        display_df['qc_change_type'] = ''
        display_df.reset_index(drop=True, inplace=True)
        roi_id_list = display_df['font_info'].apply(lambda x: x.get('roi_id'), dict()).tolist()
        display_df['line_id'] = [''.join((roi_id.get('para', ''), roi_id.get('childbox', ''), roi_id.get('subtext', ''))) for roi_id in roi_id_list]
        # Build search data
        search_df = cpt_df[['CPT_section', 'para_text', 'level_1_CPT_section']]
        search_df.rename(columns = {'para_text': 'content'}, inplace=True)

        return display_df, search_df

    def get_cpt_iqvdata(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[int], Optional[int], Optional[int]]:
        """
        Input arguments:
        id: Unique ID of the document

        Returns:
        In DICT format for the cpt section, contains three main sections:
            * Content: Actual text (or) table json
            * type: header, text or table
            * font_info: dictionary of font details
        """
        try:
            if self.iqv_document is None:
                return None, None, None, None, None

            cpt_details, tot_redact_entity, matched_redact_entity = self.read_cpt_tags()
            raw_cpt_df = pd.DataFrame(cpt_details)

            len_cpt_details = len(cpt_details)
            if len_cpt_details == 0:
                logger.warning(f"No cpt section tags are present: {len_cpt_details}")
                return None, None, None, None, None

            # Handling missing CPT tags
            if (not all(True if tag_name in raw_cpt_df.columns else False for tag_name in self.interested_tags)):
                all_columns = self.interested_tags
                all_columns.extend(raw_cpt_df.columns)
                raw_cpt_df = raw_cpt_df.reindex(columns=list(set(all_columns)), fill_value='')

            raw_cpt_df.fillna(value='', inplace=True)
            raw_cpt_df['table_index'] = raw_cpt_df['table_index'].apply(lambda x: int(float(x)) if len(x)> 0 else -1)
            unique_table_index = [table_index for table_index in set(raw_cpt_df['table_index']) if table_index > 0]
            # Populate table contents
            table_list, table_redaction_count = soa.getTOIfromProprties(soa(self.iqv_document, self.profile_details, self.entity_profile_genre), table_indexes=unique_table_index)
            table_index_dict = {int(float(item['TableIndex'])):item for item in table_list}
            raw_cpt_df['table_content'] = raw_cpt_df['table_index'].apply(lambda col: table_index_dict.get(col, ''))
            del table_list
            # Identify type of contents
            type_conditions = [raw_cpt_df['table_index'] > 0,
                               (raw_cpt_df[self.hdr_tag_name] != '') | (
                               raw_cpt_df['font_heading_flg']),
                               raw_cpt_df['image_content'] > ""]
            type_choices = ['table', 'header', "image"]
            raw_cpt_df['type'] = np.select(type_conditions, type_choices, default='text')
            display_df, search_df = self.build_display_search(raw_cpt_df)

            try:
                logger.info(f"display section: \n # of rows: {display_df.shape[0]} \n type stats: {Counter(display_df['type'])} \
                                \n unique file_section count: {display_df['file_section'].nunique()} \
                                \n file_section stats: {Counter(display_df['file_section'])} ")
                logger.info(f"search section: \n # of rows: {search_df.shape[0]} \
                                \n unique {ModuleConfig.GENERAL.SEARCH_ROLLUP_COLUMN} count: {search_df[ModuleConfig.GENERAL.SEARCH_ROLLUP_COLUMN].nunique()} \
                                \n rollup {ModuleConfig.GENERAL.SEARCH_ROLLUP_COLUMN} stats: {Counter(search_df[ModuleConfig.GENERAL.SEARCH_ROLLUP_COLUMN])}")
            except Exception as exc:
                logger.warning(f"Exception while writing INFO log on display/search section. Most likely evasive unicode chars display error")
        except Exception as exc:
            logger.exception("Exception received in cpt section iqvdata")
            logger.exception(f"Exception message: {exc}")
            return None, None, None, None, None

        return display_df, search_df, tot_redact_entity, matched_redact_entity, table_redaction_count
