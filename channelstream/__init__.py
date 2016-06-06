from datetime import datetime
from gevent.lock import RLock

__version__ = {
    'major': 0,
    'minor': 5,
    'patch': 1
}

stats = {
    'total_messages': 0,
    'total_unique_messages': 0,
    'started_on': datetime.utcnow()
}

lock = RLock()
CHANNELS = {}
USERS = {}
CONNECTIONS = {}
