from mq_service.config import Config
from microservices.email_notification import EmailNotification

def test_email_notification():
    cc=Config('simple')
    fn=EmailNotification(cc)
    data={'final':{'docId':'4c7ea27b-8a6b-4bf0-a8ed-2c1e49bbdc8c','test_case':True}}
    msg=fn.on_callback(data)
    assert msg!=None