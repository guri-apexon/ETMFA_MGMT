import logging
import pytest

from etmfa.consts import Consts as consts
from etmfa.db.db import db_context
from etmfa.db.models.amp_server_run_info import amp_server_run_info

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("id", [('unit-test-2b5a-4c8f-9f32-6d025707039b')])
def test_amp_server_models(new_app_context, id):
    _, _app_context = new_app_context
    with _app_context:
        try:
            logger.debug(f"test_amp_server_models: Processing for unit test")
            record = amp_server_run_info.query.filter(amp_server_run_info.aidoc_id == id).first()

            assert record.aidoc_id is not None and record.run_id is not None

        except Exception as ex:
            db_context.session.rollback()
            logging.error(ex)
            assert False
        db_context.session.commit()
