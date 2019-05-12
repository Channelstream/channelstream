from gevent import monkey

monkey.patch_all()

import argparse
import copy
import logging
import pprint
import os
import configparser

import gevent
from gevent.server import StreamServer

import channelstream.wsgi_app as pyramid_app
import channelstream
from channelstream.cli import CONFIGURABLE_PARAMS, SHARED_DEFAULTS
from channelstream.gc import gc_conns_forever, gc_users_forever
from channelstream.policy_server import client_handle
from channelstream.ws_app import ChatApplicationSocket
from channelstream.utils import set_config_types

from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RoutingApplication(object):
    def __init__(self, config):
        self.ws_app = WebSocketWSGIApplication(handler_cls=ChatApplicationSocket)
        self.wsgi_app = pyramid_app.make_app(config)

    def __call__(self, environ, start_response):
        if environ["PATH_INFO"] == "/ws":
            environ["ws4py.app"] = self
            return self.ws_app(environ, start_response)

        return self.wsgi_app(environ, start_response)


def main():
    config = copy.deepcopy(SHARED_DEFAULTS)

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-i", "--ini", dest="ini", help="Config file path", default=None
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        help="Print version info and exit",
        default=None,
        nargs="*",
    )
    args = parser.parse_args()

    if args.version is not None:
        print(channelstream.__version__)
        exit()

    ini_path = args.ini or os.environ.get("CHANNELSTREAM_INI")

    # set values from ini/cli
    if ini_path:
        parser = configparser.ConfigParser()
        parser.read(ini_path)
        settings = dict(parser.items("channelstream"))
        for key in CONFIGURABLE_PARAMS:
            try:
                config[key] = settings[key]
            except KeyError:
                pass
    else:
        for key in CONFIGURABLE_PARAMS:
            conf_value = os.environ.get(f"channelstream_{key}".upper())
            if conf_value is not None:
                config[key] = conf_value

    config = set_config_types(config)
    log_level = getattr(logging, (config.get("log_level") or "INFO").upper())
    logging.basicConfig(level=log_level)
    log.setLevel(log_level)
    log.debug(pprint.pformat(config))
    log.info("Starting channelstream {}".format(channelstream.__version__))
    url = "http://{}:{}".format(config["host"], config["port"])

    log.info("Starting flash policy server on port 10843")
    gevent.spawn(gc_conns_forever)
    gevent.spawn(gc_users_forever)
    server = StreamServer(("0.0.0.0", 10843), client_handle)
    server.start()
    log.info("Serving on {}".format(url))
    log.info("Admin interface available on {}/admin".format(url))
    if config["secret"] == "secret":
        log.warning("Using default secret! Remember to set that for production.")
    if config["admin_secret"] == "admin_secret":
        log.warning("Using default admin secret! Remember to set that for production.")
    log.warning(f"IP's allowed to post to API {config['allow_posting_from']}")
    server = WSGIServer(
        (config["host"], config["port"]),
        RoutingApplication(config),
        log=logging.getLogger("channelstream.WSGIServer"),
    )
    server.serve_forever()
