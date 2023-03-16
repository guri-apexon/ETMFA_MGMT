from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String
SchemaBase = declarative_base()


class MsRegistry(SchemaBase):
   __tablename__ = 'tblMsRegistry'
   service_name = Column(String, primary_key=True)
   input_queue = Column(String)
   output_queue = Column(String)
