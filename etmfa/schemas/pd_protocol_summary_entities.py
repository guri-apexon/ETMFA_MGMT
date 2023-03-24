from typing import Optional
from pydantic import BaseModel as Base


# Shared properties
class ProtocolSummaryEntitiesBase(Base):
    aidocId: Optional[str] = None
    source: Optional[str] = None
    runId: Optional[int] = None
    iqvdataSummaryEntities: Optional[str] = None
    isActive: Optional[bool] = None


# Properties to receive via API on creation
class ProtocolSummaryEntitiesCreate(ProtocolSummaryEntitiesBase):
    aidocId: str
    source: str
    runId: int
    iqvdataSummaryEntities: str
    isActive: bool


# Properties to receive via API on update
class ProtocolSummaryEntitiesUpdate(ProtocolSummaryEntitiesBase):
    pass


class ProtocolSummaryEntitiesBaseInDBBase(ProtocolSummaryEntitiesBase):
    aidocId: Optional[str] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class ProtocolSummaryEntities(ProtocolSummaryEntitiesBase):
    pass
