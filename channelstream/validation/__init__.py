import collections
import uuid

import marshmallow
from apispec.ext.marshmallow.openapi import OpenAPIConverter
from marshmallow import fields, ValidationError
from marshmallow.base import FieldABC

from channelstream.server_state import get_state

converter = OpenAPIConverter("2.0.0", schema_name_resolver=lambda: None, spec=None)


MSG_EDITABLE_KEYS = ("uuid", "timestamp", "user", "message", "edited")


def gen_uuid():
    return uuid.uuid4()


def validate_connection_id(conn_id):
    server_state = get_state()
    if conn_id not in server_state.connections:
        raise marshmallow.ValidationError("Unknown connection")


def validate_username(username):
    server_state = get_state()
    if username not in server_state.users:
        raise marshmallow.ValidationError("Unknown user")


def add_missing_fields(data, original, form_fields):
    for key, val in original.items():
        if key not in form_fields:
            data[key] = val
    return data


@converter.map_to_openapi_type("object", "object")
class UserStateDictField(fields.Dict):
    default_error_messages = {
        "invalid_value": "'{dict_key}' key is not type of string, integer, boolean or float.",
        "invalid": "Not a valid mapping type.",
    }

    def _deserialize(self, value, attr, data, partial=False):
        value = super(UserStateDictField, self)._deserialize(
            value, attr, data, partial=partial
        )
        for k in value.keys():
            if (
                not isinstance(value[k], (str, bytes))
                and not isinstance(value[k], float)
                and not isinstance(value[k], int)
                and not isinstance(value[k], bool)
                and value[k] is not None
            ):
                self.fail("invalid_value", dict_key=k)
        return value


@converter.map_to_openapi_type("string", "string")
class UserStateField(fields.Field):
    default_error_messages = {
        "invalid_value": "Value is not type of string, integer, boolean or float."
    }

    def _deserialize(self, value, attr, data, partial=False):
        if (
            not isinstance(value, str)
            and not isinstance(value, float)
            and not isinstance(value, int)
            and not isinstance(value, bool)
            and value is not None
        ):
            self.fail("invalid_value")
        return value


class ChannelstreamSchema(marshmallow.Schema):
    class Meta:
        strict = True
        ordered = True
