import logging
import re
from etmfa.consts import Consts as consts, constants

import json
import pandas as pd

from etmfa.utilities.redaction.footnotes_redaction import RedactFootNotes

logger = logging.getLogger(consts.LOGGING_NAME)


class TableRedaction():
    """
     user		redact_flag		hide_table_json_flag		return_refreshed_table_html
        (if true, redact)   (if true, donot return json)    (if true, return reconstruct html from content in properties)
    primary = 	  false				true						     false
    secondary =   true				true						     true
    QC = 		  false			    false						     true
    """
    def __init__(self,
                 redact_flag: bool = False,
                 hide_table_json_flag: bool = True,
                 return_refreshed_table_html: bool = False,
                 redact_text: str = constants.REDACT_PARAGRAPH_STR,
                 redact_profile_entities = list()
                 ):
        self.redact_flag = redact_flag
        self.hide_table_json_flag = hide_table_json_flag
        self.return_refreshed_table_html = return_refreshed_table_html
        self.span_redact_text = ''.join(['<span class="redact">', redact_text, '</span>'])
        self.redact_text = redact_text
        self.redact_profile_entities = redact_profile_entities

    def redact_entity(self, table_property):
        try:

            for entity in table_property.get('entities', list()):
                if entity.get('subcategory', '') in self.redact_profile_entities and len(
                        constants.REGEX_SPECIAL_CHAR_REPLACE.sub(r"", entity['text'])) != 0:
                    entity_adjusted_text = constants.REGEX_SPECIAL_CHAR_REPLACE.sub(r".{1}", entity['text'])
                    table_property['content'] = re.sub(entity_adjusted_text, self.span_redact_text, table_property['content'])

            return table_property
        except Exception as ex:
            logger.error(f"Exception raised in - Table Redaction - redact_entity: {str(ex)}")

    def refresh_html_table(self, properties_df_cols, properties_df):
        table_df = pd.DataFrame()
        for col_idx in properties_df_cols:
            table_df[col_idx] = [prop['content'] if prop and prop['content'] else '' for prop in properties_df[col_idx]]

        return table_df

    def refresh_footnotes(self, table_dictonary, footnote_json):

        footnote_pattern = ''.join((constants.FOOTNOTE_STR, '_'))
        table_dictonary_keys = list(table_dictonary.keys())
        for key in table_dictonary_keys:
            if key.startswith(footnote_pattern):
                del table_dictonary[key]
        table_dictonary.update(footnote_json)

        return table_dictonary

    def redact_table(self,
                     table_dictonary: dict
                     ):
        try:
            if table_dictonary:
                properties = table_dictonary.get('TableProperties')
                if properties:
                    properties = json.loads(properties)
                    properties_df = pd.DataFrame(properties)
                    properties_df_cols = properties_df.columns

                    """
                        Block that redacts the table HTML and footnotes with the redacted text
                    """
                    if self.redact_flag:
                        # Table redaction
                        for col_idx in properties_df_cols:
                            properties_df[col_idx] = [self.redact_entity(prop) if prop and prop['entities'] else prop for prop in
                                                      properties_df[col_idx]]

                        table_df = self.refresh_html_table(properties_df_cols, properties_df)

                        table_dictonary['Table'] = table_df.to_html(escape=False)

                        # Footnote redaction
                        attachment_list_properties = table_dictonary.get('AttachmentListProperties', list())

                        redactFootNotes = RedactFootNotes(attachments=attachment_list_properties,
                                                          redacted_placeholder=self.redact_text,
                                                          redact_flag=self.redact_flag,
                                                          redact_profile_entities = self.redact_profile_entities)
                        redacted_json = redactFootNotes.redact_footnotes_pipeline()

                        if redacted_json:
                            table_dictonary = self.refresh_footnotes(table_dictonary, redacted_json)

                    """
                        redact_flag == False checking this because if it True, already updated the table HTML 
                        and footnotes in the above block
                    """
                    if self.return_refreshed_table_html and self.redact_flag == False:
                        # Table refresh
                        table_df = self.refresh_html_table(properties_df_cols, properties_df)
                        table_dictonary['Table'] = table_df.to_html(escape=False)

                        # Footnote refresh
                        footnote_json = dict()
                        footnote_pattern = ''.join((
                                                   constants.FOOTNOTE_STR, '_'))
                        idx = 0
                        attachment_list_properties = table_dictonary.get('AttachmentListProperties', list())
                        for attachment in attachment_list_properties:
                            footnote_json[''.join((footnote_pattern, str(idx)))] = attachment['Text']
                            idx += 1
                        if footnote_json:
                            table_dictonary = self.refresh_footnotes(table_dictonary, footnote_json)

                    """
                        Block to delete the ROI ID's and the unredacted text from the return json
                    """
                    if self.hide_table_json_flag:
                        if 'TableProperties' in table_dictonary:
                            del table_dictonary['TableProperties']
                        if 'AttachmentListProperties' in table_dictonary:
                            del table_dictonary['AttachmentListProperties']

        except Exception as ex:
            logger.error(f"Exception raised in - Table Redaction: {str(ex)}")

        return table_dictonary
