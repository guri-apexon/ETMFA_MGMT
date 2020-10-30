import argparse
import os
from sys import argv

from etmfa.server import create_app
from etmfa.server.config import app_config
from gevent.pywsgi import WSGIServer

if __name__ == '__main__':
    config_name = 'development'
    # is_SSL = args.key != None and args.cert != None

    app = create_app(config_name)

    # print('Starting eTMFA Service at level: {}, on port: {}, SSL enabled: {} ...'.format(args.level, args.port, is_SSL))

    # if is_SSL:
    #     server = WSGIServer(('0.0.0.0', args.port), app, keyfile=args.key, certfile=args.cert)
    # else:
    server = WSGIServer(('0.0.0.0', 9001), app)

    try:
        server.serve_forever()
    except (KeyboardInterrupt):
        print('Exiting eTMFA...')
        server.stop()
