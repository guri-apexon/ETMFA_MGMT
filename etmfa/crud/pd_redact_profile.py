import logging
from typing import Optional

from etmfa.crud.base import CRUDBase
from etmfa.db.models.pd_redact_profile import PDRedactProfile
from etmfa.schemas.pd_redact_profile import (RedactProfileCreate,
                                             RedactProfileUpdate)
from sqlalchemy.orm import Session
from etmfa.consts import Consts as consts

logger = logging.getLogger(consts.LOGGING_NAME)


class CRUDRedactProfile(CRUDBase[PDRedactProfile, RedactProfileCreate, RedactProfileUpdate]):
    def get_all_active(self, db: Session) -> Optional[PDRedactProfile]:
        """
        Retrieves all active redaction profile details
        """
        try:
            return db.query(PDRedactProfile).filter(
                PDRedactProfile.isActive == True).all()
        except Exception as exc:
            logger.exception(f"Exception in retrieval of active profiles: {str(exc)}")
            return None


pd_redact_profile = CRUDRedactProfile(PDRedactProfile)
