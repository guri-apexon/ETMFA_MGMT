import logging
import pytest

from etmfa.consts import Consts as consts
from etmfa.db.db import db_context
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db import save_doc_processing

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


data_arg = {'sourceFileName': 'test-protocol', 'versionNumber': '1.0', 'protocolNumber': 'test-protocol', 'sponsor': 'test-sponsor',
            'sourceSystem': 'unit-test', 'documentStatus': 'final', 'studyStatus': None, 'amendmentNumber': 'Y', 'projectID': 'PD',
            'environment': 'dev', 'indication': 'test-indication', 'moleculeDevice': 'test-mol', 'userId': 'test-user',
            'file': 'test-protocol.pdf'}
@pytest.mark.parametrize("data_arg, id, filepath,",
                         [(data_arg, 'unit-test-046d3909-f1ca-4b73-9871', '//test/unit-test-046d3909-f1ca-4b73-9871/test-protocol.pdf'),
                          ])
def test_save_doc_processing(new_app_context, data_arg, id, filepath):
    _, _app_context = new_app_context
    with _app_context:
        try:
            logger.debug(f"test_save_doc_processing: Processing for unit test")
            save_doc_processing(data_arg, id, filepath)
            record = PDProtocolMetadata.query.filter(PDProtocolMetadata.id == id).first()

            assert record.id == id and record.documentFilePath == filepath
            PDProtocolMetadata.query.filter(PDProtocolMetadata.id == id).delete()

        except Exception as ex:
            db_context.session.rollback()
            logging.error(ex)
            assert False
        db_context.session.commit()
