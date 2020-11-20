import argparse
import os
from sys import argv

from etmfa.server import create_app
from etmfa.server.config import app_config
from gevent.pywsgi import WSGIServer

if __name__ == '__main__':
    config_name = 'development'
    app = create_app(config_name)
    server = WSGIServer(('0.0.0.0', 9001), app)

    try:
        server.serve_forever()
    except (KeyboardInterrupt):
        print('Exiting eTMFA...')
        server.stop()
