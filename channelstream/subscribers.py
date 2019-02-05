from pyramid.httpexceptions import HTTPNotAcceptable


def handle_new_request(event):
    settings = event.request.registry.settings
    event.request.handle_cors()
    if settings["enforce_https"] and event.request.scheme != "https":
        raise HTTPNotAcceptable("SSL is required")

    if settings["http_scheme"]:
        event.request.scheme = settings["http_scheme"]
