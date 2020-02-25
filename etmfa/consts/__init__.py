import threading

import gevent.local
from flask import g
from pkg_resources import get_distribution, DistributionNotFound


class Consts():
    LOGGING_NAME = 'mgmt'


class Globals:
    THREAD_LOCAL = threading.local()
    GEVENT_LOCAL = gevent.local.local()
    FLASK_LOCAL = g

    try:
        VERSION = get_distribution("etmfa_mgmt").version
    except DistributionNotFound:
        VERSION = 'debug'
