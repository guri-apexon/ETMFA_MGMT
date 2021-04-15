import pytest
from etmfa.server.config import Config
from etmfa.db import pd_fetch_summary_data
from etmfa.server import create_app
from etmfa.server.config import app_config
from gevent.pywsgi import WSGIServer


config_name = 'development'
_app_context = create_app(config_name).app_context()


@pytest.mark.parametrize("aidocid, userid",
                         [("66f3aef7-5b75-47bd-acf9-b17bceecd642", "u5555"),
                          ("b7fa3376-373c-4d7e-ace7-e882774fcd1a", "u6666"),
                          ("3da9c490-1a98-484c-b97b-a2c3ad65462c", "u7777")
                          ])
def test_QC_summary_update(aidocid, userid):
    with _app_context:
        summary_details = pd_fetch_summary_data(aidocid, userid)
        assert aidocid == summary_details