from sqlalchemy import Boolean, Column, DateTime, Integer, String
from etmfa.db.db import db_context


class PDRedactProfile(db_context.Model):
    __tablename__ = "pd_redact_profile"

    isActive = Column(Boolean(), default=False)
    subCategory = Column(String, primary_key=True)
    genre = Column(String, primary_key=True)
    description = Column(String, nullable=True)
    profile_0 = Column(Boolean(), default=False)
    profile_1 = Column(Boolean(), default=True)

    def as_dict(self):
        obj = {col.name: getattr(self, col.name) for col in self.__table__.columns}
        return obj