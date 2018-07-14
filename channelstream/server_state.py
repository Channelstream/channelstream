from datetime import datetime

from gevent.lock import RLock

STATS = {
    "total_messages": 0,
    "total_unique_messages": 0,
    "started_on": datetime.utcnow(),
}
lock = RLock()
CHANNELS = {}
USERS = {}
CONNECTIONS = {}
MESSAGE_STATUS = {"NORMAL": 1, "CATCHUP": 2}
