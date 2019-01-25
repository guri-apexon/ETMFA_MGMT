import argparse
from tms.server import create_app
from tms.server.config import app_config

from gevent.wsgi import WSGIServer

import gevent

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Translation Management Service deployment script.')

    level_opts = list(app_config.keys())
    parser.add_argument('--level', type=str,
                        help='Deployment configuration level for the application. Options include: {}'.format(str(level_opts)),
                        default='development')
    parser.add_argument('--port', type=int,
                        help='Port for Translation Management Service api to reside on',
                        default=8203)
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

    print('Starting Translation Management Service at level: {}, on port: {}, SSL enabled: {} ...'.format(args.level, args.port, is_SSL))

    if is_SSL:
        server = WSGIServer(('0.0.0.0', args.port), app, keyfile=args.key, certfile=args.cert)
    else:
        server = WSGIServer(('0.0.0.0', args.port), app)

    try:
        server.serve_forever()
    except (KeyboardInterrupt):
        print('Exiting TMS...')
        server.stop()        