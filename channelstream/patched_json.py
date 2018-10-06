from __future__ import absolute_import

import datetime
import decimal
import functools
import json
import uuid


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, complex):
            return [obj.real, obj.imag]
        elif isinstance(obj, datetime.datetime):
            r = obj.isoformat()
            if r.endswith("+00:00"):
                r = r[:-6] + "Z"
            return r
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return str(obj)
        elif isinstance(obj, datetime.time):
            r = obj.isoformat()
            if obj.microsecond:
                r = r[:12]
            return r
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, "__json__"):
            if callable(obj.__json__):
                return obj.__json__()
            else:
                return obj.__json__
        else:
            raise NotImplementedError


load = json.load
loads = json.loads
dump = json.load
dumps = functools.partial(json.dumps, indent=4, cls=ComplexEncoder)
