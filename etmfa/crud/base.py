from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from etmfa.db.db import db_context, SchemaBase

Base = db_context.make_declarative_base(model=SchemaBase)

ModelType = TypeVar("ModelType", bound=db_context.Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=Base)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=Base)


# Abstract base class for generic types
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Retrieves a record based on primary key or id"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(
        self, db: Session) -> List[ModelType]:
        """Retrieves all records by default and limit can be set"""
        return db.query(self.model).all()
    
    def get_by_userId(self, db: Session, userId: str) -> List[ModelType]:
        """Retrieves a record based on primary key or id"""
        return db.query(self.model).filter(self.model.userId == userId).all()

    def get_by_user(self, db: Session, user: str) -> Optional[ModelType]:
        """Retrieves a record based on user"""
        return db.query(self.model).filter(self.model.user == user).all()
    
