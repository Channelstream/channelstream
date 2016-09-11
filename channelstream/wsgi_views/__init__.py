"""View handlers package.
"""
import logging


from channelstream.ext_json import json
from pyramid.renderers import JSON

log = logging.getLogger(__name__)

json_renderer = JSON(serializer=json.dumps, indent=4)


def includeme(config):
    config.add_renderer('json', json_renderer)
    config.add_route('CORS_route', '/*foo', request_method='OPTIONS')
    config.add_view(handle_CORS, route_name='CORS_route', renderer='string')
    config.add_route('index', '/')
    config.add_route('demo', '/demo')
    config.add_route('admin', '/admin',
                     factory='channelstream.wsgi_views.'
                             'wsgi_security:BasicAuthFactory')
    config.add_route('admin_json', '/admin/admin.json',
                     factory='channelstream.wsgi_views.'
                             'wsgi_security:BasicAuthFactory')
    config.add_route('action', '/{action}')
    config.add_route('section_action', '/{section}/{action}')


def handle_CORS(request):
    request.handle_cors()
    return ''