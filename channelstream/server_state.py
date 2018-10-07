from datetime import datetime

from gevent.lock import RLock

STATS = {"started_on": datetime.utcnow()}
lock = RLock()


class State(object):
    def __init__(self):
        self.channels = {}
        self.connections = {}
        self.users = {}
        self.stats = {"total_messages": 0, "total_unique_messages": 0}
        self.lock = RLock()


STATES = {"0": State()}


def get_state(tenant_id="0"):
    """
    Grabs right state for specific tenant
    :param tenant_id:
    :return:
    """
    return STATES[tenant_id]
