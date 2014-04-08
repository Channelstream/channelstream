import base64
import sys
import hmac
import hashlib
import json
import time
from datetime import timedelta, datetime

# code borrowed from itsdangerous package

PY2 = sys.version_info[0] == 2

if PY2:
    text_type = unicode
else:
    text_type = str


class InvalidHMAC(Exception):
    pass


def want_bytes(s, encoding='utf-8', errors='strict'):
    if isinstance(s, text_type):
        s = s.encode(encoding, errors)
    return s


def base64_encode(string):
    """base64 encodes a single bytestring (and is tolerant to getting
    called with a unicode string).
    The resulting bytestring is safe for putting into URLs.
    """
    string = want_bytes(string)
    return base64.urlsafe_b64encode(string).strip(b'=')


def base64_decode(string):
    """base64 decodes a single bytestring (and is tolerant to getting
    called with a unicode string).
    The result is also a bytestring.
    """
    string = want_bytes(string, encoding='ascii', errors='ignore')
    return base64.urlsafe_b64decode(string + b'=' * (-len(string) % 4))


def hmac_encode(secret, endpoint):
    """Generates a HMAC hash for endpoint """
    d = int(time.time())
    h = hmac.new(secret, '%s.%s' % (endpoint.encode('utf8'), d), hashlib.sha256)
    signature = base64.b64encode(h.digest())
    return '%s.%s' % (signature, d)


def hmac_validate(secret, endpoint, other_signature):
    """Validates a HMAC hash for endpoint"""
    d = int(time.time())
    old_sig, time_split = other_signature.split('.', 1)
    old_time = int(time_split)
    h = hmac.new(secret, '%s.%s' % (endpoint.encode('utf8'), old_time), hashlib.sha256)
    signature = base64.b64encode(h.digest())
    if signature != old_sig:
        raise InvalidHMAC("Local sig: %s didnt match other sig: %s" % (
            signature, old_sig))