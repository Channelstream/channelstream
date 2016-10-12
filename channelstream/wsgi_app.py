import datetime

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON

from channelstream.ext_json import json
from channelstream.wsgi_views.wsgi_security import APIFactory


def datetime_adapter(obj, request):
    return obj.isoformat()


def make_app(server_config):
    config = Configurator(settings=server_config, root_factory=APIFactory)

    def check_function(username, password, request):
        if (password == server_config['admin_secret'] and
                username == server_config['admin_user']):
            return ('admin', username)
        return None

    authn_policy = BasicAuthAuthenticationPolicy(check_function,
                                                 realm='ChannelStream')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    json_renderer = JSON(serializer=json.dumps, indent=4)
    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    config.add_renderer('json', json_renderer)
    config.add_static_view('static', path='channelstream:static/')
    config.add_request_method('channelstream.utils.handle_cors', 'handle_cors')
    config.include('pyramid_jinja2')
    config.include('channelstream.wsgi_views')
    config.scan('channelstream.wsgi_views.server')
    config.scan('channelstream.events')
    if config.registry.settings['demo']:
        config.scan('channelstream.wsgi_views.demo')
    app = config.make_wsgi_app()
    return app
