import json
import logging
from typing import Tuple
import pandas as pd
import etmfa.utilities.elastic_ingest as ei
from etmfa_core.aidoc.IQVDocumentFunctions import IQVDocument
from etmfa.utilities.extractor import cpt_extractor
from etmfa.consts.constants import ModuleConfig
from etmfa.consts import Consts as consts
from etmfa.error import GenericMessageException

logger = logging.getLogger(consts.LOGGING_NAME)


class PrepareUpdateData:
    def __init__(self, iqv_document: IQVDocument, imagebinaries: dict,
                 profile_details: dict, entity_profile_genre: list):
        """
        Preparing section/header data with document id , user profile detials and protocol view redaction entities

            ** parameters **
        iqv_document: requested document
        profile_details: user redact profile
        entity_profile_genre: protocol view redaction entities
        """
        self.iqv_document = iqv_document
        self.imagebinaries = imagebinaries
        self.dict_orient_type = ModuleConfig.GENERAL.dict_orient_type
        self.empty_json = ModuleConfig.GENERAL.empty_json
        self.profile_details = profile_details
        self.entity_profile_genre = entity_profile_genre

    def prepare_msg(self) -> Tuple[dict, IQVDocument]:
        """
           prepare data and return as db_data  
        """
        db_data = self._prepare_db_data()
        return db_data, self.iqv_document
    
    def get_norm_cpt(self,host,port,index) -> dict:
        """
        customized reading for mcra attributes
        """
        cpt_iqvdata = cpt_extractor.CPTExtractor(self.iqv_document,self.imagebinaries,self.profile_details, self.entity_profile_genre)
        display_df, search_df, _, _ = cpt_iqvdata.get_cpt_iqvdata()
        display_dict = display_df.to_dict(orient=self.dict_orient_type)
        db_data, _= ei.ingest_doc_elastic(self.iqv_document, search_df)
        status=ei.save_elastic_doc(host,port,index,db_data)
        if not status:
            raise GenericMessageException("Failed to ingest doc to elastic")

        try:
            metadata_fields = dict()
            for key in ModuleConfig.GENERAL.es_metadata_mapping:
                metadata_fields[ModuleConfig.GENERAL.es_metadata_mapping[key]] = db_data.get(key, '')
            metadata_fields['accuracy'] = ''         
        except Exception as exc:
            logger.exception(f"Exception received in building metadata_fields step: {exc}")
        display_dict['metadata']=metadata_fields
        return display_dict


    def _prepare_db_data(self):
        """
            preparing data for requested document
        """
        iqv_document = self.iqv_document
        db_data = dict()
        db_data['iqvdoc_tagid'] = iqv_document.id
        db_data['toc'] = self.empty_json
        db_data['soa'] = self.empty_json
        db_data['summary'] = self.empty_json
        db_data['normalized_soa'] = self.empty_json

        # Elastic search ingestion
        try:
            cpt_iqvdata = cpt_extractor.CPTExtractor(iqv_document,
                                                     self.imagebinaries,
                                                     self.profile_details,
                                                     self.entity_profile_genre)
            display_df, search_df, _, _ = cpt_iqvdata.get_cpt_iqvdata()
            db_data, summary_entities = ei.ingest_doc_elastic(iqv_document, search_df)
            logger.info("Elastic search ingestion step completed")
            db_data["summary_entities"] = json.dumps(summary_entities)
            db_data['ProtocolName'] = db_data.get("protocol_name", "")
            db_data['Activity_Status'] = ''
            db_data['Completeness_of_digitization'] = ''
            db_data['Digitized_Confidence_interval'] = ''

        except Exception as exc:
            logger.exception(f"Exception received in Elastic search ingestion step: {exc}")

        # Collect additional metadata fields (for downstream applications)
        try:
            metadata_fields = dict()
            for key in ModuleConfig.GENERAL.es_metadata_mapping:
                metadata_fields[ModuleConfig.GENERAL.es_metadata_mapping[key]] = db_data.get(key, '')

            metadata_fields['accuracy'] = ''
            logger.info(f"metadata: {metadata_fields}")
        except Exception as exc:
            logger.exception(f"Exception received in building metadata_fields step: {exc}")

        # Entire file content extraction
        try:
            if display_df is not None:
                display_df['aidocid'] = iqv_document.id
                display_df['synonyms_extracted_terms'] = ''
                display_df['semantic_extraction'] = ''
                display_df["section_locked"] = False
                display_dict = display_df.to_dict(orient=self.dict_orient_type)
                display_dict['metadata'] = metadata_fields
                db_data['toc'] = json.dumps(display_dict)
                logger.info("CPT extraction step completed")

            else:
                logger.error("No data received at CPT extraction step. display_df is empty")
        except Exception as exc:
            logger.exception(f"Exception received in CPT extraction step: {exc}")

        try:
            normalized_soa = self.normalized_soa_extraction(iqv_document)
            db_data['normalized_soa'] = json.dumps(normalized_soa)
            logger.info("Normalized SOA json extraction step completed")
        except Exception as exc:
            logger.exception(f"Exception received in normalized soa extraction: {exc}")

        # Summary data
        try:
            summary_dict = list()
            for key, val in ModuleConfig.SUMMARY.summary_key_list.items():
                if key == "primary_objectives":
                    summary_dict.append((key, metadata_fields.get("objectives_section", ""), val))
                else:
                    summary_dict.append((key, metadata_fields.get(key, ""), val))

            summary_dict = pd.DataFrame(summary_dict)
            summary_dict.columns = ["field_name", "field_value", "field_header"]
            summary_dict = summary_dict.to_dict(orient=self.dict_orient_type)
            summary_dict['metadata'] = {"accuracy": ""}
            db_data['summary'] = json.dumps(summary_dict)
            logger.info("Summary extraction step completed")
        except Exception as exc:
            logger.exception(f"Exception received in Summary extraction step: {exc}")

        return display_df.to_dict(
            orient='records') if display_df is not None else dict()

    def normalized_soa_extraction(self, iqv_document):
        try:
            for kv in iqv_document.Properties:
                if kv.key == 'NormalizedSOA_JSONFilename':
                    normalized_soa_path = kv.value
                    with open(normalized_soa_path) as f:
                        soa_json_data = json.load(f)
                        return soa_json_data
        except Exception as e:
            logger.error("No Normalized SOA Json path")
