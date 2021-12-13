import logging
from etmfa.consts import Consts as consts

# Setup logger
logger = logging.getLogger(consts.LOGGING_NAME)


def test_api_health(new_app_context):
    new_app, _ = new_app_context
    client = new_app.test_client()
    with client:
        response = client.get("/pd/api/health/")
        assert response.status_code == 200
        assert (response.data).decode('utf-8') == "F5-UP"
