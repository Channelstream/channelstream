import logging

from itsdangerous import TimestampSigner
from pyramid.security import Allow, Everyone, ALL_PERMISSIONS, authenticated_userid

log = logging.getLogger(__name__)


class RequestBasicChallenge(Exception):
    pass


def is_allowed_ip(addr, config):
    if "0.0.0.0" in config["allow_posting_from"]:
        return True
    return addr in config["allow_posting_from"]


class APIFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        config = request.registry.settings
        req_url_secret = request.params.get("secret")
        req_secret = request.headers.get("x-channelstream-secret", req_url_secret)

        addr = request.environ["REMOTE_ADDR"]
        if not is_allowed_ip(addr, config):
            log.warning("IP: {} is not whitelisted".format(addr))
            return

        if req_secret:
            max_age = 60 if config["validate_requests"] else None
            signer = TimestampSigner(config["secret"])
            signer.unsign(req_secret, max_age=max_age)
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
