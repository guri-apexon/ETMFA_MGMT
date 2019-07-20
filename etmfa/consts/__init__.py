import threading
import gevent.local
from flask import g


class Consts():
	LOGGING_NAME = 'mgmt'


class Globals:
    THREAD_LOCAL = threading.local()
    GEVENT_LOCAL = gevent.local.local()
    FLASK_LOCAL = g