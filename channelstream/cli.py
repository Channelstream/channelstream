__author__ = 'ergo'

from gevent import monkey

monkey.patch_all()

import ConfigParser
import collections
import logging
import optparse


from channelstream.wsgi_app import make_app
from channelstream.ws_app import ChatApplication
from channelstream.policy_server import client_handle
from gevent.server import StreamServer
from geventwebsocket import WebSocketServer, Resource
from pyramid.settings import asbool

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
        'debug': False,
        'status_codes': {
            "offline": 0,
            "online": 1,
            "away": 2,
            "hidden": 3,
            "busy": 4,
        }
    }

    parser = optparse.OptionParser()
    parser.add_option("-i", "--ini", dest="ini",
                      help="config file location",
                      default=None)
    parser.add_option("-s", "--secret", dest="secret",
                      help="secret used to secure your requests",
                      default='secret')
    parser.add_option("-a", "--admin_secret", dest="admin_secret",
                      help="secret used to secure your admin_panel",
                      default='admin_secret')
    parser.add_option("-o", "--o", dest="host",
                      help="host ip on which the server listens to",
                      default='0.0.0.0')
    parser.add_option("-p", "--port", dest="port",
                      help="port on which the server listens to",
                      default=8000)
    parser.add_option("-d", "--debug", dest="debug",
                      help="debug",
                      default=0)
    parser.add_option("-e", "--demo", dest="demo",
                      help="debug",
                      default=False)
    parser.add_option("-x", "--allowed_post_ip", dest="allow_posting_from",
                      help="comma separated list of ip's that can post to server",
                      default="127.0.0.1"
    )
    (options, args) = parser.parse_args()
    if options.ini:
        parser = ConfigParser.ConfigParser()
        parser.read(options.ini)
        try:
            config['debug'] = parser.getboolean('channelstream', 'debug')
        except ConfigParser.NoOptionError as e:
            pass
        try:
            config['demo'] = parser.getboolean('channelstream', 'demo')
        except ConfigParser.NoOptionError as e:
            pass
        try:
            config['port'] = parser.getint('channelstream', 'port')
        except ConfigParser.NoOptionError as e:
            pass
        try:
            config['host'] = parser.get('channelstream', 'host')
        except ConfigParser.NoOptionError as e:
            pass
        try:
            config['secret'] = parser.get('channelstream', 'secret')
        except ConfigParser.NoOptionError as e:
            pass
        try:
            config['admin_secret'] = parser.get('channelstream', 'admin_secret')
        except ConfigParser.NoOptionError as e:
            pass
        try:
            ips = [ip.strip() for ip in parser.get('channelstream',
                                               'allow_posting_from').split(',')]
            config['allow_posting_from'].extend(ips)
        except ConfigParser.NoOptionError as e:
            pass
        try:
            config['demo_app_url'] = parser.get('channelstream', 'demo_app_url')
        except ConfigParser.NoOptionError as e:
            pass
    else:
        config['debug'] = int(options.debug)
        config['port'] = int(options.port)
        config['demo'] = asbool(options.demo)
        config['host'] = options.host
        config['secret'] = options.secret
        config['admin_secret'] = options.admin_secret
        config['allow_posting_from'].extend(
            [ip.strip() for ip in options.allow_posting_from.split(',')])

    logging.basicConfig(level=logging.INFO)
    print 'Starting flash policy server on port 10843'
    server = StreamServer(('0.0.0.0', 10843), client_handle)
    server.start()
    print 'Serving on http://%s:%s' % (config['host'], config['port'])
    app_dict = collections.OrderedDict({
        '^/ws.*': ChatApplication,
        '^/*': make_app(config)
    })
    WebSocketServer(
        (config['host'], config['port']),
        Resource(app_dict),
        debug=False
    ).serve_forever()
