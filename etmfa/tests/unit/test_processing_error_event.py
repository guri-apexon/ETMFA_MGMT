import logging
import pytest

from etmfa.consts import Consts as consts
from etmfa.db.db import db_context
from etmfa.db.models.pd_protocol_metadata import PDProtocolMetadata
from etmfa.db import received_documentprocessing_error_event

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("data_dict, insert_flag, comments",
                         [({'id': '78338974-bc26-4153-8f0f-24c9d292f203', 'error_code': 000, 'service_name': 'mgmt', 'error_message': 'unit-test-error-msg'}, 1, "Normal insertion"),
                            ({'id': '9de1df71-2547-4a13-a087-d0570b45aa67', 'error_code': 000, 'service_name': 'mgmt', 'error_message': 'unit-test-error-msg'}, 0, "No insertion")
                          ])
def test_processing_error_event(new_app_context,  data_dict,  insert_flag, comments):
    try:
        _, _app_context = new_app_context
        with _app_context:
            logger.debug(f"test_processing_error_event: Processing for unit test")
            if insert_flag:
                received_documentprocessing_error_event(data_dict)
                record = PDProtocolMetadata.query.filter(PDProtocolMetadata.id == data_dict.get('id')).first()
                assert record.errorCode == data_dict['error_code'] and record.status == 'ERROR'
            elif insert_flag == 0:
                assert True

    except Exception as ex:
        db_context.session.rollback()
        logging.error(ex)
        assert False
