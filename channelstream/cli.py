from gevent import monkey

monkey.patch_all()

import copy
import logging
import argparse

from six.moves import configparser

from gevent.server import StreamServer
from pyramid.settings import asbool

import channelstream.wsgi_app as pyramid_app
from channelstream.gc import gc_conns_forever, gc_users_forever
from channelstream.policy_server import client_handle
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

SHARED_DEFAULTS = {
    'secret': 'secret',
    'admin_user': 'admin',
    'admin_secret': 'admin_secret',
    'gc_conns_after': 30,
    'gc_channels_after': 3600 * 72,
    'wake_connections_after': 5,
    'allow_posting_from': '127.0.0.1',
    'port': 8000,
    'host': '0.0.0.0',
    'debug': False,
    'demo': False,
    'allow_cors': ''
}


def cli_start():
    config = copy.deepcopy(SHARED_DEFAULTS)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-?', '--help', action='help')
    parser.add_argument('-i', '--ini', dest='ini',
                        help='config file location',
                        default=None)
    parser.add_argument('-s', '--secret', dest='secret',
                        help='secret used to secure your requests')
    parser.add_argument('-u', '--admin_username', dest='admin_user',
                        help='Administrator username')
    parser.add_argument('-a', '--admin_secret', dest='admin_secret',
                        help='secret used to secure your admin_panel')
    parser.add_argument('-host', '--host', dest='host',
                        help='host ip on which the server listens to')
    parser.add_argument('-p', '--port', type=int, dest='port',
                        help='port on which the server listens to')
    parser.add_argument('-d', '--debug', dest='debug', help='debug')
    parser.add_argument('-e', '--demo', dest='demo', help='demo enabled')
    parser.add_argument('-x', '--allowed_post_ip', dest='allow_posting_from',
                        help='comma separated list of ip\'s '
                             'that can post to server')
    parser.add_argument('-c', '--allow_cors', dest='allow_cors',
                        help='comma separated list of domains\'s '
                             'that can connect to server')
    args = parser.parse_args()

    parameters = (
        'debug', 'port', 'host', 'secret', 'admin_user', 'admin_secret',
        'demo', 'allow_posting_from', 'allow_cors')

    if args.ini:
        parser = configparser.ConfigParser()
        parser.read(args.ini)
        settings = dict(parser.items('channelstream'))
        for key in parameters:
            try:
                config[key] = settings[key]
            except KeyError:
                pass
    else:
        for key in parameters:
            conf_value = getattr(args, key)
            if conf_value:
                config[key] = conf_value

    # convert types
    config['debug'] = asbool(config['debug'])
    config['port'] = int(config['port'])
    config['demo'] = asbool(config['demo'])

    for key in ['allow_posting_from', 'allow_cors']:
        if not config[key]:
            continue
        try:
            listed = [ip.strip() for ip in config[key].split(',')]
            config[key] = listed
        except ValueError:
            pass

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
        log.warning('\n\n!! NEVER run the demo in production !!\n\n')

    server = WSGIServer((config['host'], config['port']),
                        RoutingApplication(config))
    server.serve_forever()
