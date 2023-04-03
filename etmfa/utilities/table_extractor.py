import json
import re
import logging
import pandas as pd
import numpy as np
import ast
from etmfa.utilities import data_extractor_utils as utils
from etmfa.consts.constants import ModuleConfig
from etmfa.consts import Consts as consts

logger = logging.getLogger(consts.LOGGING_NAME)


# The below section is for reconstruction of table from the updated iqvxml
# after extraction service
class SOAResponse:
    def __init__(self, iqv_document, profile_details: dict, entity_profile_genre: list):

        self.tableTypeDict = {'SOA': r'\b(?:Assessments|Assessment|Schedule)\b'}
        self.iqv_document = iqv_document

        self.profile_details = profile_details
        self.entity_profile_genre = entity_profile_genre

    def drop_duplicate_header(self,df):
        row_header = list(pd.Series(
            df[(df['RowIndex'] % 1000).isin([1, 2, 3, 4])][
                'RowIndex'].unique()).nsmallest(4, keep='first'))
        Header_rows_list = (df[df['RowIndex'].isin(row_header)].groupby(['RowIndex']))['FullText'].apply(list).astype(str)
        All_rows_list=(df[~(df['RowIndex'].isin(row_header))].groupby(['RowIndex']))['FullText'].apply(list).astype(str)
        out_list = []
        for header in Header_rows_list:
            header = set(ast.literal_eval(header))
            len_header = len(header)
            out = All_rows_list.apply(lambda x: x.index if ((len(header.intersection(set(ast.literal_eval(x)))))/len_header) > 0.7 else None)

            out_list.extend(list((out[out.notna()]).index.values))

        return (out_list)

    def header_finder(self, df):
        try:
            row_header=(df[(df.IsHeaderCell.isin(['1.0','2','1']))]['RowIndex']%1000).unique()
            all_header=list(pd.Series((df[(df.IsHeaderCell.isin(['1.0','2','1']))]['RowIndex']).unique()))
            keep_header=list(pd.Series((df[(df.IsHeaderCell.isin(['1.0','2','1']))]['RowIndex']).unique()).nsmallest(len(row_header),keep='first'))
            drop_rows=list(set(all_header)-set(keep_header))
            keep_header=((np.array(keep_header)%1000)-1).astype('int')
        except Exception as e :
            drop_rows=[-1]
            keep_header=[-1]

        return (drop_rows,keep_header)

    def findRgx(self,text,regex=r'\b(?:Assessments|Assessment|Schedule)\b'):
        try :
            rx = re.compile(regex,re.IGNORECASE)
            rxx = rx.search(text)
            if rxx :
                return_val=1
            else:
                return_val=0
        except Exception as e :
            return_val=0
        return(return_val)

    tableTypeDict={'SOA':r'\b(?:Assessments|Assessment|Schedule)\b'}

    def getTOIfromProprties(self,roi=[],toi=None,table_indexes=[]):
        try:
            df=pd.DataFrame()
            poi=list(ModuleConfig.GENERAL.std_tags_dict.values())
            acceptroi=False
            if toi:
                for para in self.iqv_document.DocumentTables:
                    for prop in para.Properties:
                        if prop.key== 'TableName' and self.findRgx(prop.value,self.tableTypeDict[toi])==1 :
                            roi.append (para.id)
            elif len(table_indexes) > 0:
                acceptroi=False
            else :
                acceptroi=True

            dictTableMetaList=[]
            nlp_entities_count = 0
            for table in self.iqv_document.DocumentTables:
                if ((table.id in roi) or acceptroi or any([True if (prop.key == 'TableIndex' and
                                                                    int(float(prop.value)) in
                                                                    table_indexes)
                                                           else False for prop in table.Properties])):
                    dictTableMeta=dict()
                    for prop in table.Properties:
                        if (prop.key in poi) or ((prop.key).startswith('Footnote')):
                            dictTableMeta[prop.key]=('' if prop.value=='nan' else prop.value)
                        elif prop.key.startswith('AttachmentId'):
                            if 'AttachmentList' not in dictTableMeta:
                                dictTableMeta['AttachmentList'] = list()
                                dictTableMeta['entities'] = list()
                            dictTableMeta['AttachmentList'].append('' if prop.value == 'nan' else eval(prop.value))
                            dictTableMeta['AttachmentList'][-1]['qc_change_type'] = ''

                            _, redaction_entities = utils.get_redaction_entities(
                                level_roi=table.Attachments[int(dictTableMeta['AttachmentList'][-1]['AttachmentIndex'])])

                            _, nlp_entities_list_aligned = utils.align_redaction_with_subtext(
                                dictTableMeta['AttachmentList'][-1]['Text'], redaction_entities)

                            dictTableMeta['AttachmentList'][-1]['entities'] = nlp_entities_list_aligned
                            if len(nlp_entities_list_aligned) > 0:
                                redacted_txt = '{} {}'.format(dictTableMeta['AttachmentList'][-1]['Key'], dictTableMeta['AttachmentList'][-1]['Text'])
                                redacted_txt = utils.redact_text(text=redacted_txt, text_redaction_entity=nlp_entities_list_aligned, redact_profile_entities=self.profile_details, redact_flg=self.entity_profile_genre)
                                dictTableMeta['FootnoteText_{}'.format(len(dictTableMeta['AttachmentList']) - 1)] = redacted_txt
                    for row in table.ChildBoxes:
                        for column in row.ChildBoxes:
                            for textblock in column.ChildBoxes:
                                dictTable=dict()
                                dfList=[]
                                column_index_list=[]
                                for propT in textblock.Properties:
                                    if (propT.key!='ColIndex' and  propT.key in poi ):
                                        dictTable[propT.key]=propT.value
                                    elif propT.key=='ColIndex':
                                        column_index_list=propT.value[1:-1].split(',')
                                # Start For handling redaction and QC workflow
                                nlp_entities_list = list()
                                for entity in column.NLP_Entities:
                                    for property in entity.Properties:
                                        if property.key == ModuleConfig.GENERAL.REDACTION_SUBCATEGORY_KEY:
                                            nlp_entities_list.append(
                                                {'standard_entity_name': entity.standard_entity_name,
                                                 'subcategory': property.value, 'text': entity.text,
                                                 'start_pos': entity.start,
                                                 'text_len': len(entity.text),
                                                 'end_pos': entity.start + len(entity.text) - 1,
                                                 'confidence': entity.confidence})
                                            nlp_entities_count += 1
                                # END For handling redaction and QC workflow

                                for col in column_index_list :
                                    dictTableCol=dict()
                                    dictTableCol=dictTable.copy()
                                    dictTableCol['ColIndex']=col.strip()
                                    # Start For handling redaction and QC workflow
                                    matched_entity_set, nlp_entities_list_aligned = utils.align_redaction_with_subtext(dictTableCol.get('FullText', ''), nlp_entities_list)
                                    dictTableCol['table_properties'] = dict()
                                    dictTableCol['table_properties']['entities'] = nlp_entities_list_aligned
                                    dictTableCol['table_properties']['content'] = dictTableCol.get('FullText', '')
                                    dictTableCol['table_properties']['roi_id'] = {'table_roi_id':table.id,
                                                                                  'row_roi_id':row.id,
                                                                                  'column_roi_id':column.id,
                                                                                  'datacell_roi_id':textblock.id
                                                                                  }
                                    dictTableCol['table_properties']['table_index'] = float(dictTableCol.get('TableIndex', '0')) - 1
                                    dictTableCol['table_properties']['qc_change_type'] = ''
                                    if len(nlp_entities_list_aligned) > 0:
                                        redacted_txt = dictTableCol['FullText']
                                        redacted_txt = utils.redact_text(text=redacted_txt, text_redaction_entity=nlp_entities_list_aligned,
                                                                         redact_profile_entities=self.profile_details,
                                                                         redact_flg=self.entity_profile_genre)
                                        dictTableCol['FullText'] = redacted_txt
                                    # END For handling redaction and QC workflow
                                    dfList.append(dictTableCol)
                                    df=df.append(pd.DataFrame(dfList))

                    dictTableMetaList.append(dictTableMeta)

            # For handling the footnotes that occur in different TableROI due to which the footnotes in TableROI apart from first ROI were not getting populated in the resultssoa
            if len(dictTableMetaList) > 1:
                dictTableMetaList_1 = list()
                tableIndex = None
                dictTableMeta = dict()
                footnote_idx = 0
                for tableMeta in dictTableMetaList:
                    if tableIndex != tableMeta.get('TableIndex', None):
                        if dictTableMeta:
                            dictTableMetaList_1.append(dictTableMeta)
                        tableIndex = tableMeta.get('TableIndex', None)
                        footnote_idx = 0
                        dictTableMeta = dict()
                        dictTableMeta['SectionHeaderPrintPage'] = tableMeta.get('SectionHeaderPrintPage', None)
                        dictTableMeta['TableIndex'] = tableMeta.get('TableIndex', None)
                        dictTableMeta['TableName'] = tableMeta.get('TableName', None)

                    if 'AttachmentList' in tableMeta and 'AttachmentListProperties' not in dictTableMeta:
                        dictTableMeta['AttachmentListProperties'] = tableMeta.get('AttachmentList', list())
                    elif 'AttachmentList' in tableMeta and 'AttachmentListProperties' in dictTableMeta:
                        dictTableMeta['AttachmentListProperties'].extend(tableMeta.get('AttachmentList', None))

                    for key,val in tableMeta.items():
                        if key.startswith('FootnoteText'):
                            dictTableMeta['FootnoteText_'+str(footnote_idx)] = val
                            footnote_idx += 1


                if dictTableMeta and len(dictTableMetaList_1) > 0 and dictTableMetaList_1[-1]['TableIndex'] != dictTableMeta['TableIndex']:
                    dictTableMetaList_1.append(dictTableMeta)

                if dictTableMeta and len(dictTableMetaList_1) == 0:
                    dictTableMetaList_1.append(dictTableMeta)

                if dictTableMetaList_1:
                    dictTableMetaList = dictTableMetaList_1

            result=[]

            if len(df) > 1:
                df[['TableIndex','RowIndex','ColIndex']] = df[['TableIndex','RowIndex','ColIndex']].astype(float)
                df=df.sort_values(['TableIndex','RowIndex','ColIndex','IsHeaderCell']).groupby(['TableIndex','RowIndex','ColIndex'])[['TableIndex','FullText', 'table_properties', 'ColIndex','RowIndex','IsHeaderCell']].last()
                df=df.reset_index(drop=True)
                toi=df.TableIndex.unique()
                logger.info("Finalization Total Number of SOA Found : {}".format(len(toi)))
                for tabseq in toi:
                    resultreturn=dict()
                    col_header=dict()
                    resulttable=pd.DataFrame()
                    resulttable=df[(df.TableIndex==tabseq)]
                    drop_rows,keep_header=self.header_finder(df=resulttable)
                    drop_rows.extend(self.drop_duplicate_header(df=resulttable))
                    resulttable=df[(df.TableIndex==tabseq) & (~(df.RowIndex.isin(drop_rows)))]
                    resulttable=resulttable.reset_index(drop=True)
                    resulttable_redact = resulttable.copy(deep=True)
                    # Generating table structure
                    resulttable=resulttable.pivot(index='RowIndex',columns='ColIndex',values='FullText')
                    resulttable=resulttable.fillna('')
                    resulttable=resulttable.replace('nan','')
                    # Generating table structure redaction tags
                    resulttable_redact=resulttable_redact.pivot(index='RowIndex',columns='ColIndex',values='table_properties')
                    resulttable_redact=resulttable_redact.fillna('')
                    resulttable_redact=resulttable_redact.replace('nan','')

                    keep_header=[int(x) for x in keep_header]
                    append=1
                    for tabIndex in [i for i in dictTableMetaList if i]:
                        if ((int(float(tabIndex['TableIndex'])) == int(float(tabseq))) and append==1):
                            resulttable=resulttable.reset_index(drop=True)
                            resultreturn['Table']=resulttable.to_html(escape=False)
                            resultreturn['TableProperties'] = return_table_formated_data(resulttable_redact.to_json(orient="records"))
                            resultreturn.update(tabIndex)
                            resultreturn['Header']=keep_header
                            result.append(resultreturn)
                            append=0

            return (result, nlp_entities_count)

        except Exception as e :
            logger.error("Error SOA :Reconstruction of table failed with error : {}".format(e))
            return ({}, 0)



def return_table_formated_data(data):
    table_properties_formater = []
    for item in eval(data):
        column_list = []
        roi_id = ''
        for k,v in item.items():
            if isinstance(v,dict):
                roi_id = v.get("roi_id",{}).get('row_roi_id')
                column_list.append({
                          "col_indx": len(column_list),
                          "op_type": None,
                          "cell_id": v.get("roi_id",{}).get("datacell_roi_id",""),
                          "value": v.get('content')
                        })
            else:
                roi_id = ''
                column_list.append({
                          "col_indx": len(column_list),
                          "op_type": None,
                          "cell_id": "",
                          "value": ""
                        })

        new_dict = {"row_indx": len(table_properties_formater), "roi_id": roi_id, "op_type": None, "columns":column_list}
        table_properties_formater.append(new_dict)
    return json.dumps(table_properties_formater)