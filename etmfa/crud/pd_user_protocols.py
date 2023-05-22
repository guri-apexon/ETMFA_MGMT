import logging
from typing import Any, Optional

from etmfa.crud.base import CRUDBase
from etmfa.db.models.pd_user_protocols import \
    PDUserProtocols as PD_User_Protocols
from etmfa.db.models import User
from etmfa.schemas.pd_user_protocols import (UserProtocolCreate,
                                             UserProtocolUpdate)
from sqlalchemy.orm import Session
from etmfa.consts import Consts as consts

logger = logging.getLogger(consts.LOGGING_NAME)


class CRUDUserProtocols(CRUDBase[PD_User_Protocols, UserProtocolCreate, UserProtocolUpdate]):
    def get_by_id(self, db: Session, *, id: Any, userId: Any) -> Optional[PD_User_Protocols]:
        return db.query(PD_User_Protocols).filter(PD_User_Protocols.id == id).filter(
            PD_User_Protocols.userId == userId).first()

    def get_by_userid_protocol(self, db: Session, userid: Any, protocol: Any) -> PD_User_Protocols:
        """Retrieves record from table"""
        return db.query(self.model).filter(PD_User_Protocols.userId == userid).filter(
            PD_User_Protocols.protocol == protocol).filter(PD_User_Protocols.isActive=='1').first()

    def get_user_type_from_userid(self, db: Session, userid: str):
        """Retrieve user_type for the user"""
        return db.query(User).filter(User.username.in_(("u" + userid, "q" + userid, userid))).first()


pd_user_protocols = CRUDUserProtocols(PD_User_Protocols)
