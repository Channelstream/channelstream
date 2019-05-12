import copy
import uuid

import marshmallow
from pyramid.renderers import render
from pyramid.settings import asbool


def handle_cors(request):
    settings = request.registry.settings
    if not settings["allow_cors"]:
        request.response.headers.add("Access-Control-Allow-Origin", "*")
    else:
        origin = request.headers.get("Origin") or "<>"
        for domain in settings["allow_cors"]:
            if domain in origin:
                request.response.headers.add("Access-Control-Allow-Origin", "*")
                break

    request.response.headers.add("XDomainRequestAllowed", "1")
    request.response.headers.add(
        "Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE, PATCH"
    )
    request.response.headers.add(
        "Access-Control-Allow-Headers",
        "Content-Type, Depth, User-Agent, "
        "X-File-Size, X-Requested-With, "
        "If-Modified-Since, X-File-Name, "
        "Cache-Control, Pragma, Origin, "
        "Connection, Referer, Cookie",
    )
    request.response.headers.add("Access-Control-Max-Age", "86400")


def swagger_ui_script_template(request, spec_route_name, **kwargs):
    """
    Generates the <script> code that bootstraps Swagger UI, it will be injected
    into index template
    :param request:
    :param spec_route_name:
    :return:
    """
    return render("templates/explorer.jinja2", value=(), request=request)


def uuid_from_string(str_uuid):
    try:
        return uuid.UUID(str_uuid)
    except (ValueError, AttributeError):
        raise marshmallow.ValidationError("Wrong UUID format")


def process_catchup(m):
    copied = copy.deepcopy(m)
    copied["catchup"] = True
    copied.pop("pm_users", None)
    copied.pop("exclude_users", None)
    copied.pop("no_history", None)
    return copied


def set_config_types(config):
    """
    convert raw config values to proper types
    :param config:
    :return:
    """
    config = copy.deepcopy(config)
    config["debug"] = asbool(config["debug"])
    config["port"] = int(config["port"])
    config["validate_requests"] = asbool(config["validate_requests"])
    config["enforce_https"] = asbool(config["enforce_https"])
    if not config["cookie_secret"]:
        config["cookie_secret"] = str(uuid.uuid4())

    if config["http_scheme"] not in ["http", "https"]:
        config["http_scheme"] = ""

    for key in ["allow_posting_from", "allow_cors"]:
        if not config[key]:
            continue
        # if those keys are strings from ini convert to lists of individual values
        if isinstance(config[key], str):
            try:
                listed = [ip.strip() for ip in config[key].split(",") if ip.strip()]
                config[key] = listed
            except ValueError:
                pass
    return config
