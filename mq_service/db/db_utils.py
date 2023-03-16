from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from . import create_db_context
from .schemas import MsRegistry

class DbMixin:
    def __init__(self):
        self.engine, self.session_local = create_db_context()

    def release_context(self):
        del self.engine
        del self.session_local

    def read_by_id(self, table_name, id):
        with self.session_local() as session:
            return session.query(table_name).get(id)

    def write_many(self, data_list):
        with self.session_local() as session:
            session.add_all(data_list)
            session.commit()

    def write_unique(self, data):
        with self.session_local() as session:
            try:
                session.add(data)
                session.commit()
            except IntegrityError as e:
                if not isinstance(e.orig, UniqueViolation):
                    raise e

# only for refernce ,do direct


def convert_Json_to_schema(data: dict, Schema):
    return Schema(**data)


class Store(DbMixin):
    def register_service(self, data: MsRegistry):
        self.write_unique(data)

    def get_service(self, name):
        return self.get_by_id(MsRegistry, name)
