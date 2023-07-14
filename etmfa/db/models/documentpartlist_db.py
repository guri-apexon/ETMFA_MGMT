from etmfa.db import db_context


class DocumentpartslistDb(db_context.Model):
    __tablename__ = "documentpartslist_db"
    id = db_context.Column(db_context.VARCHAR(128),primary_key=True,nullable=False)
    doc_id = db_context.Column(db_context.TEXT)
    link_id = db_context.Column(db_context.TEXT)
    link_id_level2 = db_context.Column(db_context.TEXT, default='')
    link_id_level3 = db_context.Column(db_context.TEXT, default='')
    link_id_level4 = db_context.Column(db_context.TEXT, default='')
    link_id_level5 = db_context.Column(db_context.TEXT, default='')
    link_id_level6 = db_context.Column(db_context.TEXT, default='')
    link_id_subsection1 = db_context.Column(db_context.TEXT)
    link_id_subsection2 = db_context.Column(db_context.TEXT)
    link_id_subsection3 = db_context.Column(db_context.TEXT)
    hierarchy = db_context.Column(db_context.VARCHAR(128),nullable=False)
    iqv_standard_term = db_context.Column(db_context.TEXT)
    parent_id = db_context.Column(db_context.TEXT)
    group_type = db_context.Column(db_context.TEXT)
    sequence_id = db_context.Column(db_context.INTEGER,nullable=False)
    userId = db_context.Column(db_context.VARCHAR(100))
    last_updated = db_context.Column(db_context.DateTime(timezone=True), nullable=True)
    num_updates = db_context.Column(db_context.INTEGER, default=0)
   
    def as_dict(self):
        obj = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return obj 