import logging
from datetime import datetime, timedelta

import gevent

from channelstream.server_state import get_state

log = logging.getLogger(__name__)


def gc_conns():
    server_state = get_state()
    with server_state.lock:
        start_time = datetime.utcnow()
        threshold = start_time - timedelta(seconds=15)
        collected_conns = []
        # collect every ref in chanels
        # remove connections from channels
        for channel in server_state.channels.values():
            for username, conns in list(channel.connections.items()):
                for conn in conns:
                    if conn.last_active < threshold:
                        channel.connections[username].remove(conn)
                        collected_conns.append(conn)
                channel.after_parted(username)
        # remove old conns from users and connection dictionaries
        for conn in collected_conns:
            if conn.username in server_state.users:
                if conn in server_state.users[conn.username].connections:
                    server_state.users[conn.username].connections.remove(conn)
            if conn.id in server_state.connections:
                del server_state.connections[conn.id]
            # make sure connection is closed after we garbage
            # collected it from our list
            conn.queue = None
            if conn.socket:
                try:
                    conn.socket.close()
                except Exception:
                    raise
        log.debug(
            "gc_conns() removed:%s time %s"
            % (len(collected_conns), datetime.utcnow() - start_time)
        )


def gc_users():
    server_state = get_state()
    with server_state.lock:
        counter = 0
        start_time = datetime.utcnow()
        threshold = datetime.utcnow() - timedelta(days=1)
        for user in list(server_state.users.values()):
            if user.last_active < threshold:
                counter += 1
                server_state.users.pop(user.username)
        log.debug(
            "gc_users() removed:%s time %s" % (counter, datetime.utcnow() - start_time)
        )


def gc_users_forever():
    while True:
        try:
            gc_users()
        except Exception as exc:
            log.error(exc)
        gevent.sleep(60)


def gc_conns_forever():
    while True:
        try:
            gc_conns()
        except Exception as exc:
            log.error(exc)
        gevent.sleep(1)
