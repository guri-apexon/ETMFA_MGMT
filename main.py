from sys import argv
from gevent.pywsgi import WSGIServer
from etmfa.server import create_app

if __name__ == '__main__':
    config_name = 'development'

    app = create_app(config_name)
    server = WSGIServer(('0.0.0.0', 8002), app)

    try:
        server.serve_forever()
    except (KeyboardInterrupt):
        server.stop()
