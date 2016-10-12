from pyramid.events import NewRequest
from pyramid.events import subscriber


@subscriber(NewRequest)
def mysubscriber(event):
    scheme = event.request.headers.get('HTTP_X_SCHEME', '')
    scheme = event.request.headers.get('HTTP_X_URL_SCHEME', scheme)
    if scheme:
        event.request.environ['wsgi.url_scheme'] = scheme