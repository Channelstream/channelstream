from gevent import monkey

monkey.patch_all()

from six.moves import configparser
import logging
import argparse

from gevent.server import StreamServer
from pyramid.settings import asbool
from channelstream.gc import gc_conns_forever, gc_users_forever
from channelstream.policy_server import client_handle
import channelstream.wsgi_app as pyramid_app
from channelstream.ws_app import ChatApplicationSocket

from ws4py.server.geventserver import WebSocketWSGIApplication, \
    WebSocketWSGIHandler, WSGIServer

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RoutingApplication(object):
    def __init__(self, config):
        self.ws_app = WebSocketWSGIApplication(
            handler_cls=ChatApplicationSocket)
        self.wsgi_app = pyramid_app.make_app(config)

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == '/ws':
            environ['ws4py.app'] = self
            return self.ws_app(environ, start_response)

        return self.wsgi_app(environ, start_response)


def cli_start():
    config = {
        'secret': '',
        'admin_secret': '',
        'gc_conns_after': 30,
        'gc_channels_after': 3600 * 72,
        'wake_connections_after': 5,
        'allow_posting_from': [],
        'port': 8000,
        'host': '0.0.0.0',
        'debug': False
    }

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-?", "--help", action="help")
    parser.add_argument("-i", "--ini", dest="ini",
                        help="config file location",
                        default=None)
    parser.add_argument("-s", "--secret", dest="secret",
                        help="secret used to secure your requests",
                        default='secret')
    parser.add_argument("-a", "--admin_secret", dest="admin_secret",
                        help="secret used to secure your admin_panel",
                        default='admin_secret')
    parser.add_argument("-host", "--host", dest="host",
                        help="host ip on which the server listens to",
                        default='0.0.0.0')
    parser.add_argument("-p", "--port", type=int, dest="port",
                        help="port on which the server listens to",
                        default=8000)
    parser.add_argument("-d", "--debug", dest="debug",
                        help="debug",
                        default=0)
    parser.add_argument("-e", "--demo", dest="demo",
                        help="demo enabled",
                        default=False)
    parser.add_argument("-x", "--allowed_post_ip", dest="allow_posting_from",
                        help="comma separated list of ip's "
                             "that can post to server",
                        default="127.0.0.1"
                        )
    args = parser.parse_args()
    if args.ini:
        parser = configparser.ConfigParser()
        parser.read(args.ini)

        non_optional_parameters = (
            'debug', 'port', 'host', 'secret', 'admin_secret',
            'demo_app_url', 'demo')
        for key in non_optional_parameters:
            try:
                config[key] = parser.get('channelstream', key)
            except configparser.NoOptionError:
                pass

        try:
            ips = [ip.strip() for ip in parser.get(
                'channelstream', 'allow_posting_from').split(',')]
            config['allow_posting_from'].extend(ips)
        except configparser.NoOptionError:
            pass

    else:
        config['debug'] = args.debug
        config['port'] = args.port
        config['demo'] = asbool(args.demo)
        config['host'] = args.host
        config['secret'] = args.secret
        config['admin_secret'] = args.admin_secret
        config['allow_posting_from'].extend(
            [ip.strip() for ip in args.allow_posting_from.split(',')])

    # convert types
    config['debug'] = int(config['debug'])
    config['port'] = int(config['port'])
    config['demo'] = asbool(args.demo)

    log_level = logging.DEBUG if config['debug'] else logging.INFO
    logging.basicConfig(level=log_level)

    url = 'http://{}:{}'.format(config['host'], config['port'])

    log.info('Starting flash policy server on port 10843')
    gc_conns_forever()
    gc_users_forever()
    server = StreamServer(('0.0.0.0', 10843), client_handle)
    server.start()
    log.info('Serving on {}'.format(url))
    log.info('Admin interface available on {}/admin'.format(url))
    if config['demo']:
        log.info('Demo enabled, visit {}/demo'.format(url))

    server = WSGIServer((config['host'], config['port']),
                        RoutingApplication(config))
    server.serve_forever()
