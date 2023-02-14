import threading

import gevent.local
from flask import g
from pkg_resources import get_distribution, DistributionNotFound


class Consts():
    LOGGING_NAME = 'mgmt'
    LOGGING_WF= 'work_flow_manager'


class Globals:
    THREAD_LOCAL = threading.local()
    GEVENT_LOCAL = gevent.local.local()
    FLASK_LOCAL = g

    try:
        VERSION = get_distribution("pd-mgmt").version
    except DistributionNotFound:
        VERSION = 'debug'
