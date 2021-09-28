import datetime
import logging

import pytest
from etmfa.consts import Consts as consts
from etmfa.db import get_record_by_userid_protocol, update_user_protocols, config
from etmfa.db.db import db_context
from etmfa.db.models.pd_user_protocols import PDUserProtocols

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


@pytest.mark.parametrize("insert_flg, user_id, protocol, expected_user_role, expected_redact_profile, comments",
                         [(True, "1034911", "SSR_1002-043", config.UPLOADED_USERROLE, config.USERROLE_REDACTPROFILE_MAP.get(config.UPLOADED_USERROLE), "New protocol for the user"),
                         (False, "1034911", "SSR_1002-043", config.UPLOADED_USERROLE, config.USERROLE_REDACTPROFILE_MAP.get(config.UPLOADED_USERROLE), "Existing protocol for the user")
                          ])
def test_follow_protocol_as_primary(new_app_context, insert_flg, user_id, protocol,expected_user_role, expected_redact_profile, comments):
    _, _app_context = new_app_context
    with _app_context:
        current_utctime = datetime.datetime.utcnow()

        if insert_flg:
            test_user_protocol = PDUserProtocols.query.filter(PDUserProtocols.userId == user_id, PDUserProtocols.protocol == protocol).delete()
            logging.info(f"Unit test {comments}: Cleared # of rows of [PDUserProtocols: {test_user_protocol}]")
            db_context.session.commit()

        _ = update_user_protocols(user_id = user_id, project_id = "", protocol_number = protocol)
        db_record = get_record_by_userid_protocol(user_id, protocol)

        assert len(db_record) == 1
        assert db_record[0].lastUpdated > current_utctime
        assert db_record[0].userRole == expected_user_role
        assert db_record[0].redactProfile == expected_redact_profile
        assert db_record[0].follow == True
        assert db_record[0].isActive == True

        if insert_flg:
            assert db_record[0].lastUpdated == db_record[0].timeCreated
