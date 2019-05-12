import logging
from pyramid.view import exception_view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPForbidden, HTTPFound

log = logging.getLogger(__name__)


@exception_view_config(context="marshmallow.ValidationError", renderer="json")
def marshmallow_invalid_data(context, request):
    request.response.status = 422
    log.error("Request had incorrect payload")
    try:
        log.debug(context.messages)
        log.debug(request.text)
    except Exception as exc:
        log.warning(u"Can't convert debug messages: %s" % exc)
    return context.messages


@exception_view_config(context="itsdangerous.BadTimeSignature", renderer="json")
@exception_view_config(context="itsdangerous.BadSignature", renderer="json")
def itsdangerous_signer_error(context, request):
    request.response.status = 401
    log.error("Request had incorrect signature")
    return {"request": "Bad Signature"}


@forbidden_view_config()
def unauthorized_handler(context, request, renderer="json"):
    if (
        request.matched_route
        and request.matched_route.pattern.startswith("/admin")
        or "api-explorer" in request.url
    ):
        url = request.route_url("admin_action", action="sign_in")
        return HTTPFound(url)
    return HTTPForbidden()
