from sqlalchemy import Column, String
from etmfa.db.db import db_context


class PdEmailTemplates(db_context.Model):
    
    __tablename__ = "pd_email_templates"


    id = Column(String, primary_key=True)
    event = Column(String, nullable=True)
    email_body = Column(String, nullable=True)
    subject = Column(String, nullable=True)
