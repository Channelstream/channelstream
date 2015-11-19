"""View handlers package.
"""
import logging


log = logging.getLogger(__name__)


def includeme(config):
    config.add_route('index', '/')
    config.add_route('demo', '/demo')
    config.add_route('admin', '/admin',
                     factory='channelstream.wsgi_views.'
                             'wsgi_security:BasicAuthFactory')
    config.add_route('action', '/{action}')
    config.add_route('section_action', '/{section}/{action}')
