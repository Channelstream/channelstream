from pyramid.events import NewRequest
from pyramid.events import subscriber


@subscriber(NewRequest)
def use_prefix(event):
    # rewrite prefix if X-Script-Name header is present
    script_name = event.request.headers.get("X_SCRIPT_NAME", "")
    if script_name:
        event.request.environ["SCRIPT_NAME"] = script_name
        path_info = event.request.environ["PATH_INFO"]
        if path_info.startswith(script_name):
            event.request.environ["PATH_INFO"] = path_info[len(script_name) :]

    # make sure http/https can be controlled
    scheme = event.request.headers.get("X_SCHEME", "")
    scheme = event.request.headers.get("X_URL_SCHEME", scheme)
    if scheme:
        event.request.environ["wsgi.url_scheme"] = scheme
