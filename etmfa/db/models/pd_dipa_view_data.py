from etmfa.db.db import db_context
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, func

from datetime import datetime
import uuid


class PDDipaViewdata(db_context.Model):
    """Class to create """
    __tablename__ = "pd_dipa_view_data"

    id = db_context.Column(db_context.String(128), primary_key=True)
    doc_id = db_context.Column(db_context.String(128))
    link_id_1 = db_context.Column(db_context.String(128))
    link_id_2 = db_context.Column(db_context.String(128))
    link_id_3 = db_context.Column(db_context.String(128))
    link_id_4 = db_context.Column(db_context.String(128))
    link_id_5 = db_context.Column(db_context.String(128))
    link_id_6 = db_context.Column(db_context.String(128))
    category = db_context.Column(db_context.String(200))
    dipa_data = Column(JSONB)
    lastEditedBy = db_context.Column(db_context.String(128))
    editorUserId = db_context.Column(db_context.String(128))
    editCount = db_context.Column(db_context.String(128))
    timeCreated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.utcnow)
    timeUpdated = db_context.Column(db_context.DateTime(timezone=True), default=datetime.utcnow,
                                    onupdate=datetime.utcnow)


class DipaViewHelper:
    """This class contains helper function to perform utilities calls/functions on dipa view data"""

    @staticmethod
    def upsert(_id, data_dict):
        """this function is used to update dipa view data into pd_dipa_view_data table"""
        session = db_context.session()
        if _id:
            obj = session.query(PDDipaViewdata).get(_id)
            obj.editCount = int(obj.editCount) + 1
            obj.editorUserId = data_dict['editorUserId']
            for attr, value in data_dict.items():
                if value:
                    setattr(obj, attr, value)
            session.commit()
        return {"Status": "Success"}