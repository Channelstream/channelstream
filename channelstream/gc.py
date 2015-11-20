import logging
from datetime import datetime, timedelta

import gevent

import channelstream

log = logging.getLogger(__name__)


def gc_conns():
    with channelstream.lock:
        start_time = datetime.utcnow()
        threshold = start_time - timedelta(seconds=15)
        collected_conns = []
        # collect every ref in chanels
        # remove connections from channels
        for channel in channelstream.CHANNELS.itervalues():
            for username, conns in channel.connections.items():
                for conn in conns:
                    if conn.last_active < threshold:
                        channel.connections[username].remove(conn)
                        collected_conns.append(conn)
                channel.after_parted(username)
        # remove old conns from users and connection dictionaries
        for conn in collected_conns:
            if conn.username in channelstream.USERS:
                if conn in channelstream.USERS[conn.username].connections:
                    channelstream.USERS[conn.username].connections.remove(conn)
            if conn.id in channelstream.CONNECTIONS:
                del channelstream.CONNECTIONS[conn.id]
            # make sure connection is closed after we garbage
            # collected it from our list
            if conn.socket:
                try:
                    conn.socket.ws.close()
                except Exception:
                    raise
        log.debug('gc_conns() time %s' % (datetime.utcnow() - start_time))


def gc_users():
    with channelstream.lock:
        start_time = datetime.utcnow()
        threshold = datetime.utcnow() - timedelta(days=1)
        for user in channelstream.USERS.values():
            if user.last_active < threshold:
                channelstream.USERS.pop(user.username)
        log.debug('gc_users() time %s' % (datetime.utcnow() - start_time))


def gc_users_forever():
    try:
        gc_users()
    finally:
        gevent.spawn_later(60, gc_users_forever)


def gc_conns_forever():
    try:
        gc_conns()
    finally:
        gevent.spawn_later(1, gc_conns_forever)
