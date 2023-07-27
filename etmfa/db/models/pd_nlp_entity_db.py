from sqlalchemy import Column, String
from etmfa.db.db import db_context


class NlpEntityDb(db_context.Model):

    __tablename__ = "nlp_entity_db"

    id = Column(String(128), primary_key=True)
    doc_id = Column(String, nullable=True)
    link_id = Column(String, nullable=True)
    link_id_level2 = Column(String, nullable=True)
    link_id_level3 = Column(String, nullable=True)
    link_id_level4 = Column(String, nullable=True)
    link_id_level5 = Column(String, nullable=True)
    link_id_level6 = Column(String, nullable=True)
    link_id_subsection1 = Column(String, nullable=True)
    link_id_subsection2 = Column(String, nullable=True)
    link_id_subsection3 = Column(String, nullable=True)
    hierarchy = Column(String(128), primary_key=True)
    iqv_standard_term = Column(String, nullable=True)
    parent_id = Column(String, nullable=True)
    group_type = Column(String, nullable=True)
    process_source = Column(String, nullable=True)
    text = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    entity_key = Column(String, nullable=True)
    entity_class = Column(String, nullable=True)
    entity_index = Column(String, nullable=True)
    entity_xref = Column(String, nullable=True)
    ontology = Column(String, nullable=True)
    ontology_version = Column(String, nullable=True)
    ontology_item_code = Column(String, nullable=True)
    standard_entity_name = Column(String, nullable=True)
    confidence = Column(String, nullable=True)
    start = Column(String, nullable=True)
    text_len = Column(String, nullable=True)
    dts = Column(String, nullable=True)
    

