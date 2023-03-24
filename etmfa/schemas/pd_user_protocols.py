from typing import Optional
from datetime import datetime
from pydantic import Field
from pydantic import BaseModel as Base


# Shared properties
class UserProtocolBase(Base):
    userId: Optional[str] = None
    protocol: Optional[str] = None
    userRole: Optional[str] = None
    userCreated: Optional[str] = None
    userUpdated: Optional[str] = None


# Properties to receive via API on creation
class UserProtocolCreate(UserProtocolBase):
    isActive: bool
    userId: str
    protocol: str
    follow: bool = True
    userRole: str = "secondary"
    userCreated: str
    userCreated: str
    timeCreated: datetime
    lastUpdated: datetime
    userUpdated: str 


class UserFollowProtocol(Base):
    userId: str
    protocol: str
    follow: bool = True
    userRole: Optional[str] = "secondary"


class UserProtocolAdd(Base):
    userId: str
    protocol: str
    projectId: Optional[str] = "pid"
    userRole: str
    follow: bool


# For Soft Deleting Making isActive False
class UserProtocolSoftDelete(Base):
    userId: str = Field(...)
    protocol: str = Field(...)
    isActive: bool = Field(...)


# Properties to receive via API on update
class UserProtocolUpdate(UserProtocolBase):
    pass
    

class UserProtocolInDBBase(UserProtocolBase):
    id: Optional[str] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class UserProtocol(UserProtocolInDBBase):
    pass

