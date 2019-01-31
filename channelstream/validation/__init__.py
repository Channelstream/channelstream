import collections
import uuid

import marshmallow
from apispec.ext.marshmallow.openapi import OpenAPIConverter
from marshmallow import fields, ValidationError
from marshmallow.base import FieldABC

from channelstream.server_state import get_state

converter = OpenAPIConverter("2.0.0", schema_name_resolver=lambda: None, spec=None)


MSG_EDITABLE_KEYS = ("uuid", "timestamp", "user", "message", "edited")


try:
    base_types = (unicode, basestring)
except NameError:
    base_types = (str,)


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

    def _deserialize(self, value, attr, data):
        value = super(UserStateDictField, self)._deserialize(value, attr, data)
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

    def _deserialize(self, value, attr, data):
        if (
            not isinstance(value, base_types)
            and not isinstance(value, float)
            and not isinstance(value, int)
            and not isinstance(value, bool)
            and value is not None
        ):
            self.fail("invalid_value")
        return value


# backported from marshmallow 3.x
@converter.map_to_openapi_type("object", "object")
class BackportedDict(fields.Field):
    """A dict field. Supports dicts and dict-like objects. Optionally composed
    with another `Field` class or instance.

    Example: ::

        numbers = fields.Dict(values=fields.Float(), keys=fields.Str())

    :param Field values: A field class or instance for dict values.
    :param Field keys: A field class or instance for dict keys.
    :param kwargs: The same keyword arguments that :class:`Field` receives.

    .. note::
        When the structure of nested data is not known, you may omit the
        `values` and `keys` arguments to prevent content validation.

    .. versionadded:: 2.1.0
    """

    default_error_messages = {"invalid": "Not a valid mapping type."}

    def __init__(self, values=None, keys=None, **kwargs):
        super(BackportedDict, self).__init__(**kwargs)
        if values is None:
            self.value_container = None
        elif isinstance(values, type):
            if not issubclass(values, FieldABC):
                raise ValueError(
                    '"values" must be a subclass of ' "marshmallow.base.FieldABC"
                )
            self.value_container = values()
        else:
            if not isinstance(values, FieldABC):
                raise ValueError(
                    '"values" must be of type ' "marshmallow.base.FieldABC"
                )
            self.value_container = values
        if keys is None:
            self.key_container = None
        elif isinstance(keys, type):
            if not issubclass(keys, FieldABC):
                raise ValueError(
                    '"keys" must be a subclass of ' "marshmallow.base.FieldABC"
                )
            self.key_container = keys()
        else:
            if not isinstance(keys, FieldABC):
                raise ValueError('"keys" must be of type ' "marshmallow.base.FieldABC")
            self.key_container = keys

    def _add_to_schema(self, field_name, schema):
        super(BackportedDict, self)._add_to_schema(field_name, schema)
        if self.value_container:
            self.value_container.parent = self
            self.value_container.name = field_name
        if self.key_container:
            self.key_container.parent = self
            self.key_container.name = field_name

    def _serialize(self, value, attr, obj):
        if value is None:
            return None
        if not self.value_container and not self.key_container:
            return value
        if isinstance(value, collections.Mapping):
            values = value.values()
            if self.value_container:
                values = [
                    self.value_container._serialize(item, attr, obj) for item in values
                ]
            keys = value.keys()
            if self.key_container:
                keys = [self.key_container._serialize(key, attr, obj) for key in keys]
            return dict(zip(keys, values))
        self.fail("invalid")

    def _deserialize(self, value, attr, data):
        if not isinstance(value, collections.Mapping):
            self.fail("invalid")
        if not self.value_container and not self.key_container:
            return value

        errors = collections.defaultdict(dict)
        values = list(value.values())
        keys = list(value.keys())
        if self.key_container:
            for idx, key in enumerate(keys):
                try:
                    keys[idx] = self.key_container.deserialize(key)
                except ValidationError as e:
                    errors[key]["key"] = e.messages
        if self.value_container:
            for idx, item in enumerate(values):
                try:
                    values[idx] = self.value_container.deserialize(item)
                except ValidationError as e:
                    values[idx] = e.data
                    key = keys[idx]
                    errors[key]["value"] = e.messages
        result = dict(zip(keys, values))

        if errors:
            raise ValidationError(errors, data=result)

        return result


class ChannelstreamSchema(marshmallow.Schema):
    class Meta:
        strict = True
        ordered = True
