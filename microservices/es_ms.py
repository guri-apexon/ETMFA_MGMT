
from mq_service import MicroServiceWrapper, ExecutionContext, Config
from multiprocessing import Process
from .common import GenericException
import json
from etmfa_core.aidoc.io.load_xml_db_ext import GetIQVDocumentFromDB_with_doc_id
from etmfa.utilities.extractor.prepare_cpt_section_data import PrepareUpdateData
from etmfa.utilities.redaction.protocol_view_redaction import ProtocolViewRedaction
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mq_service.config import Config
from etmfa.db import Protocoldata
from sqlalchemy import Integer, String, DateTime, Boolean
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata, MetaDataTableHelper
from etmfa.consts.constants import LM_MAPPED_FIELDS,EXCLUDED_LM_ACCORDIANS,SUMMARY_TYPES
from datetime import datetime
from collections import defaultdict
from etmfa_core.postgres_db_schema import  IqvkeyvaluesetDb
from sqlalchemy import and_


class ElasticIngestion(ExecutionContext):
    def __init__(self, config):
        self.config = config
        elastic_details = config.ELASTIC_DETAILS
        self.elastic_host = elastic_details['ELASTIC_HOST']
        self.elastic_port = elastic_details['ELASTIC_PORT']
        self.elastic_index = elastic_details['ELASTIC_INDEX']
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True,
                                    pool_size=1, max_overflow=-1, echo=False,
                                    pool_use_lifo=True, pool_recycle=1800)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)
        self.conn = self.engine.raw_connection()
        ExecutionContext.__init__(self, config.CONTEXT_MAX_ACTIVE_TIME)
        self.meta_helper_obj = MetaDataTableHelper()

    def on_init(self):
        """
        intialization if any needed
        """
        return True

    def convert_pd_type(self, key, val):
        ctype, cformat = SUMMARY_TYPES.get(key, (None, None))
        if ctype == 'date':
            return datetime.strptime(val, cformat) if val else None
        elif ctype == 'int':
            return int(val)
        else:
            return str(val)

    def update_existing_props(self, obj, data):
        for key,val in data.items():
            if hasattr(obj, key):
                val = self.convert_pd_type(key, val)
                if val:
                    setattr(obj, key, val)


    def update_data_to_tables(self,aidoc_id,protocol_data_str,mapped_meta_fields,lm_accordians):
        with self.SessionLocal() as session:
            curr_data = session.query(Protocoldata).filter(
                Protocoldata.id == aidoc_id).first()
            if not curr_data:
                pd_data = Protocoldata(
                    id=aidoc_id, userId='mgmt', iqvdataToc=protocol_data_str)
                session.add(pd_data)
            else:
                curr_data.iqvdataToc = protocol_data_str
            meta_data = session.query(PDProtocolMetadata).get(aidoc_id)
            self.update_existing_props(meta_data, mapped_meta_fields)
            for accordian_name,accordian_data in lm_accordians.items():
                if accordian_name in EXCLUDED_LM_ACCORDIANS:
                    continue
                if not self.meta_helper_obj.check_field_exist(session,aidoc_id,accordian_name):
                    self.meta_helper_obj.add_field(session,aidoc_id,accordian_name)
                    self.meta_helper_obj.add_field_data(session,aidoc_id,accordian_name,accordian_data)
                else:
                    self.meta_helper_obj.add_update_attribute(
                        session, aidoc_id, accordian_name, accordian_data)

            session.commit()

    def get_entities(self, doc_id):
        with self.SessionLocal() as session:
            ent_list=session.query(IqvkeyvaluesetDb.key,IqvkeyvaluesetDb.value,IqvkeyvaluesetDb.confidence).filter(and_(
                IqvkeyvaluesetDb.doc_id == doc_id, IqvkeyvaluesetDb.hierarchy == 'document',
                     IqvkeyvaluesetDb.parent_id == doc_id, IqvkeyvaluesetDb.group_type == 'Properties')).all()
            return {ent[0]:ent for ent in ent_list}

    def on_callback(self, msg_data):
        """
        return: original response or what should be sent next.
        """
        msg = list(msg_data.values())[0]
        key = 'docId' if 'docId' in msg else 'doc_id'
        aidoc_id = msg[key]
        link_level, link_id = 0, ""
        ent_map=self.get_entities(aidoc_id)
        accordians,mapped_meta_fields=defaultdict(list),{}
        for lm_name,(db_name,display_name,group_name) in LM_MAPPED_FIELDS.items():
            _,attr_val,confidence=ent_map.get(lm_name,(None,None,None))
            if (not attr_val) or (not group_name):
                continue
            attr_item={"attribute_name":db_name , "attribute_type": "string",
                                        "attribute_value": attr_val,
                                       "display_name": display_name, "confidence": confidence}
            if group_name=='summary_extended':
                mapped_meta_fields[db_name]=attr_val
            accordians[group_name].append(attr_item)

        iqv_document = GetIQVDocumentFromDB_with_doc_id(
            self.conn, aidoc_id, link_level, link_id)
        if iqv_document is None:
            raise GenericException(f"{aidoc_id} is not present in database")

        protocol_view_redaction = ProtocolViewRedaction(
            db=msg_data.get('db'), user_id='', protocol='')
        finalized_iqvxml = PrepareUpdateData(iqv_document, {},
                                             protocol_view_redaction.profile_details,
                                             protocol_view_redaction.entity_profile_genre)
        mcra_dict = finalized_iqvxml.get_norm_cpt(
            self.elastic_host, self.elastic_port, self.elastic_index)
        mcra_dict['columns'] = ["section_level", "CPT_section", "type", "content", "font_info",
                                "level_1_CPT_section", "file_section", "file_section_num", "file_section_level", "seq_num"]
        protocol_data_str = str(json.dumps(mcra_dict))
        self.update_data_to_tables(
            aidoc_id,protocol_data_str,mapped_meta_fields,accordians)
        return msg_data

    def on_release(self):
        """
        resource if any needs to be released
        """
        return True


class ElasticIngestionRunner(Process):
    def __init__(self, service_name="es_ingestion"):
        self.service_name = service_name
        Process.__init__(self)

    def run(self):
        config = Config(self.service_name)
        mw = MicroServiceWrapper(config)
        mw.run(ElasticIngestion)
