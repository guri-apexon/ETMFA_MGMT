from typing import Optional, Tuple, Any
import psycopg2
from etmfa_core.aidoc.io.load_xml_db_ext import \
    GetIQVDocumentFromDB_with_imagebinaries
import logging
from etmfa_core.aidoc.IQVDocumentFunctions import IQVDocument
from etmfa.consts import Consts as consts
from etmfa.db.db import db_context

logger = logging.getLogger(consts.LOGGING_NAME)


def get_document_object(aidoc_id: str, link_level: int, link_id: int) -> Optional[Tuple[IQVDocument, Any]]:
    """
    :param aidoc_id: document id
    :param link_level: level of headers in toc
    :param link_id: link id of particular section
    :returns: requested section/header data
    """
    connection = None
    try:
        connection = db_context.engine.raw_connection()
        headers_only = False
        include_images = True
        iqv_document, image_binaries = GetIQVDocumentFromDB_with_imagebinaries(
            connection, aidoc_id, headers_only, link_level, link_id,
            include_images=include_images)
    except (Exception, psycopg2.Error) as error:
        logger.exception(f"Failed to get connection to postgresql : {error}, {aidoc_id}")
        return None, None
    finally:
        if connection:
            connection.close()
    return iqv_document, image_binaries
