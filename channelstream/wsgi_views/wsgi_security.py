import six
from itsdangerous import TimestampSigner
from pyramid.security import (Allow,
                              Everyone,
                              ALL_PERMISSIONS,
                              authenticated_userid)


class RequestBasicChallenge(Exception):
    pass


class APIFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        config = request.registry.settings
        req_url_secret = request.params.get('secret')
        req_secret = request.headers.get('x-channelstream-secret',
                                         req_url_secret)

        if request.environ['REMOTE_ADDR'] not in config['allow_posting_from']:
            return
        if req_secret:
            signer = TimestampSigner(config['secret'])
            unsigned = signer.unsign(req_secret)
            if not six.PY2:
                unsigned = unsigned.decode('utf8')
            if request.path != unsigned:
                return
        else:
            return
        self.__acl__ = [(Allow, Everyone, ALL_PERMISSIONS)]


class BasicAuthFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        user = authenticated_userid(request)
        if not user:
            raise RequestBasicChallenge()
        self.__acl__ = [(Allow, Everyone, ALL_PERMISSIONS)]
