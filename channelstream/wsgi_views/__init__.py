"""View handlers package.
"""
import logging


log = logging.getLogger(__name__)


def includeme(config):
    config.add_static_view("static", path="channelstream:static/")
    config.add_route("CORS_route", "/*foo", request_method="OPTIONS")
    config.add_view(handle_CORS, route_name="CORS_route", renderer="string")
    config.add_route("index", "/")
    config.add_route("demo", "/demo")
    config.add_route("openapi_spec", "/openapi.json")
    config.add_route(
        "admin",
        "/admin",
        factory="channelstream.wsgi_views." "wsgi_security:BasicAuthFactory",
    )
    config.add_route(
        "admin_json",
        "/admin/admin.json",
        factory="channelstream.wsgi_views." "wsgi_security:BasicAuthFactory",
    )
    # legacy API
    config.add_route("legacy_connect", "/connect")
    config.add_route("legacy_subscribe", "/subscribe")
    config.add_route("legacy_unsubscribe", "/unsubscribe")
    config.add_route("legacy_user_state", "/user_state")
    config.add_route("legacy_message", "/message")
    config.add_route("legacy_channel_config", "/channel_config")
    config.add_route("legacy_info", "/info")

    # listening API
    config.add_route("api_listen", "/listen")
    config.add_route("api_listen_ws", "/ws")
    config.add_route("api_disconnect", "/disconnect")

    config.add_route("section_action", "/{section}/{action}")


def handle_CORS(request):
    request.handle_cors()
    return ""
