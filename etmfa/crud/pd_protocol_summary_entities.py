import json
from typing import Any, Optional
from sqlalchemy.orm import Session
from etmfa.crud.base import CRUDBase
from etmfa.db.models.pd_protocol_summary_entities import ProtocolSummaryEntities as PDProtocolSummaryEntities
from etmfa.schemas.pd_protocol_summary_entities import ProtocolSummaryEntitiesCreate, ProtocolSummaryEntitiesUpdate


class CRUDProtocols(CRUDBase[PDProtocolSummaryEntities, ProtocolSummaryEntitiesCreate, ProtocolSummaryEntitiesUpdate]):
    @staticmethod
    def get_protocol_summary_entities(db: Session, aidocId: Any) -> Optional[PDProtocolSummaryEntities]:
        """Retrieves a record based on primary key or id"""
        summary_entities = {}
        summary_db_records = db.query(PDProtocolSummaryEntities.aidocId,
                                      PDProtocolSummaryEntities.source,
                                      PDProtocolSummaryEntities.runId,
                                      PDProtocolSummaryEntities.iqvdataSummaryEntities,
                                      ).filter(PDProtocolSummaryEntities.aidocId == aidocId,
                                               PDProtocolSummaryEntities.isActive == True).first()

        if summary_db_records and summary_db_records.iqvdataSummaryEntities:
            try:
                summary_entities = json.loads(json.loads(summary_db_records.iqvdataSummaryEntities))
            except Exception:
                ...
        return summary_entities


pd_protocol_summary_entities = CRUDProtocols(PDProtocolSummaryEntities)
