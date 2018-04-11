import functools

SCHEMA_REGISTRY = []
VIEW_REGISTRY = []


def openapi_doc_schema(schema_name, **kwargs):
    """
    :param schema_name:
    :param kwargs:
    :return:

    Gathers marshmallow schema information
    """
    def r_decorator(f):
        SCHEMA_REGISTRY.append({'name': schema_name, 'item': f})

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    return r_decorator


def openapi_doc_view(route_name, **kwargs):
    """
    :param route_name:
    :param kwargs:
    :return:

    Gathers pyramid view information

    """
    def r_decorator(f):
        VIEW_REGISTRY.append({'name': route_name, 'item': f,
                              '__doc__': f.__doc__})

        @functools.wraps(f)
        def wrapper(context, request):
            return f(request)

        return wrapper

    return r_decorator
