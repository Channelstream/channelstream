import socket
import logging

log = logging.getLogger(__name__)

POLICY = '<cross-domain-policy><allow-access-from domain="*" ' \
         'to-ports="*" /></cross-domain-policy>\0'
POLICYREQUEST = "<policy-file-request/>"


def client_handle(sock, address):
    log.info("%s:%s: Connection accepted." % address)
    sock.settimeout(3)
    try:
        input = sock.recv(128)
        if input.startswith(POLICYREQUEST):
            sock.sendall(POLICY)
            log.info("%s:%s: Policy sent. Closing connection." % address)
        else:
            log.info("%s:%s: Wrong payload. Closing connection." % address)
    except socket.timeout:
        log.info("%s:%s: Timeout" % address)
    sock.close()
