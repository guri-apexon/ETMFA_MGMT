
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
from etmfa.consts.constants import SUMMARY_KEY_META_FIELDS_MAP, SUMMARY_ATTR_REV_MAP, SUMMARY_TYPES, _SummaryConfig
from datetime import datetime


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
        for key, (val, _) in data.items():
            if hasattr(obj, key):
                val = self.convert_pd_type(key, val)
                if val:
                    setattr(obj, key, val)

    def on_callback(self, msg_data):
        """
        return: original response or what should be sent next.
        """
        msg = list(msg_data.values())[0]
        key = 'docId' if 'docId' in msg else 'doc_id'
        aidoc_id = msg[key]
        link_level, link_id = 0, ""
        iqv_document = GetIQVDocumentFromDB_with_doc_id(
            self.conn, aidoc_id, link_level, link_id)
        if iqv_document is None:
            raise GenericException(f"{aidoc_id} is not present in database")

        protocol_view_redaction = ProtocolViewRedaction(
            user_id='', protocol='')
        finalized_iqvxml = PrepareUpdateData(iqv_document, {},
                                             protocol_view_redaction.profile_details,
                                             protocol_view_redaction.entity_profile_genre)
        mcra_dict = finalized_iqvxml.get_norm_cpt(
            self.elastic_host, self.elastic_port, self.elastic_index)
        mcra_dict['columns'] = ["section_level", "CPT_section", "type", "content", "font_info",
                                "level_1_CPT_section", "file_section", "file_section_num", "file_section_level", "seq_num"]
        protocol_data_str = str(json.dumps(mcra_dict))
        mapped_meta_fields = {SUMMARY_KEY_META_FIELDS_MAP.get(mkey, mkey): (mval, _SummaryConfig.summary_key_list.get(mkey, mkey))
                              for mkey, mval in mcra_dict['metadata'].items()}
        summary_attributes = [{"attribute_name": attr_name, "attribute_type": "string", "attribute_value": attr_val,
                               "display_name": display_name}
                              for attr_name, (attr_val, display_name) in mapped_meta_fields.items()]

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
            self.meta_helper_obj.add_update_attribute(
                session, aidoc_id, MetaDataTableHelper.SUMMARY_EXTENDED, summary_attributes)
            session.commit()
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
