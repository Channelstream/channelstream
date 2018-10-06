import datetime
import uuid

from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.security import NO_PERMISSION_REQUIRED

from channelstream import patched_json as json
from channelstream.wsgi_views.wsgi_security import APIFactory


def datetime_adapter(obj, request):
    return obj.isoformat()


def uuid_adapter(obj, request):
    return str(obj)


def make_app(server_config):
    config = Configurator(
        settings=server_config, root_factory=APIFactory, default_permission="access"
    )
    config.include("pyramid_jinja2")

    def check_function(username, password, request):
        if (
            password == server_config["admin_secret"]
            and username == server_config["admin_user"]
        ):
            return "admin", username
        return None

    authn_policy = BasicAuthAuthenticationPolicy(check_function, realm="ChannelStream")
    authz_policy = ACLAuthorizationPolicy()

    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    json_renderer = JSON(serializer=json.dumps, indent=4)
    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    json_renderer.add_adapter(uuid.UUID, uuid_adapter)
    config.add_renderer("json", json_renderer)

    config.add_subscriber(
        "channelstream.subscribers.handle_new_request", "pyramid.events.NewRequest"
    )
    config.add_request_method("channelstream.utils.handle_cors", "handle_cors")
    config.include("channelstream.wsgi_views")
    config.scan("channelstream.wsgi_views.server")
    config.scan("channelstream.wsgi_views.error_handlers")
    config.scan("channelstream.events")

    config.include("pyramid_apispec.views")
    config.pyramid_apispec_add_explorer(
        spec_route_name="openapi_spec",
        script_generator="channelstream.utils:swagger_ui_script_template",
        permission=NO_PERMISSION_REQUIRED,
    )
    app = config.make_wsgi_app()
    return app
