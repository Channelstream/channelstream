from datetime import datetime
from gevent.lock import RLock

__version__ = {
    'major': 0,
    'minor': 4,
    'patch': 0
}

stats = {
    'total_messages': 0,
    'total_unique_messages': 0,
    'started_on': datetime.utcnow()
}

lock = RLock()
