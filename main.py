import argparse
from etmfa.server import create_app
from etmfa.server.config import app_config

from gevent.pywsgi import WSGIServer

import gevent

if __name__ == '__main__':
    import os
    os.environ["PATH"] += os.pathsep + 'C:/Users/q1019814/oracle/instantclient_19_3/'

    parser = argparse.ArgumentParser(description='eTMFA Service deployment script.')

    level_opts = list(app_config.keys())
    parser.add_argument('--level', type=str,
                        help='Deployment configuration level for the application. Options include: {}'.format(str(level_opts)),
                        default='development')
    parser.add_argument('--port', type=int,
                        help='Port for eTMFA Service api to reside on',
                        default=9002)
    parser.add_argument('--key', type=str,
                    help='SSL key file',
                    default=None)
    parser.add_argument('--cert', type=str,
                    help='SSL certificate file',
                    default=None)

    args = parser.parse_args()

    config_name = args.level
    is_SSL = args.key != None and args.cert != None

    app = create_app(config_name, ssl_enabled=is_SSL)

    print('Starting eTMFA Service at level: {}, on port: {}, SSL enabled: {} ...'.format(args.level, args.port, is_SSL))

    if is_SSL:
        server = WSGIServer(('0.0.0.0', args.port), app, keyfile=args.key, certfile=args.cert)
    else:
        server = WSGIServer(('0.0.0.0', args.port), app)

    try:
        server.serve_forever()
    except (KeyboardInterrupt):
        print('Exiting eTMFA...')
        server.stop()        