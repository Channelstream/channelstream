from apispec.utils import load_operations_from_docstring, load_yaml_from_docstring


try:
    import basestring
    string_type = basestring
except ImportError:
    string_type = str

def is_string(val):
    return isinstance(val, string_type)

ALL_METHODS = ('get', 'post', 'put', 'patch', 'delete', 'head', 'options')


def add_pyramid_paths(
        spec, route_name, request=None, request_method=None, operations=None, **kwargs):
    """

    Adds a route and view info to spec

    :param spec:
        ApiSpec object
    :param route_name:
        Route name to inspect
    :param request:
        Request object, if `None` then `get_current_request()` will be used
    :param request_method:
        Request method predicate
    :param operations:
        Operations dict that will be used instead of introspection
    :param kwargs:
        Additional kwargs for predicate matching
    :return:

    """
    from pyramid.threadlocal import get_current_request
    if request is None:
        request = get_current_request()

    registry = request.registry
    introspector = registry.introspector
    route = introspector.get('routes', route_name)
    views = introspector.related(route)

    # needs to be rewritten to internal name
    if request_method:
        kwargs['request_methods'] = request_method
        # kwargs.setdefault('route_name', route_name)

    for view in views:
        matches = True
        for kw in kwargs.keys():
            # request_methods can be either a list of strings or a string
            # so lets normalize via sets
            if kw == 'request_methods':
                if is_string(kwargs[kw]):
                    kwargs[kw] = [kwargs[kw]]
                methods = view.get(kw) or ALL_METHODS
                if is_string(methods):
                    methods = [methods]
                if not set(kwargs[kw] or []).intersection(methods):
                    matches = False
            else:
                if not view.get(kw) == kwargs[kw]:
                    matches = False

        if not matches:
            continue

        final_operations = {}

        # views can be class based
        if view.get('attr'):
            global_meta =load_operations_from_docstring(view['callable'].__doc__)
            if global_meta:
                final_operations.update(global_meta)
            f_view = getattr(view['callable'], view['attr'])
        # or just function callables
        else:
            f_view = view.get('callable')

        if operations is None:
            methods = view.get('request_methods')
            view_operations = load_operations_from_docstring(f_view.__doc__)
            if not view_operations:
                view_operations = {}
                if is_string(methods):
                    methods = [methods]
                if not methods:
                    methods = ALL_METHODS[:]
                operation = load_yaml_from_docstring(f_view.__doc__)
                if operation:
                    for method in methods:
                        view_operations[method.lower()] = operation
            final_operations.update(view_operations)
        else:
            final_operations = operations
        spec.add_path(route['pattern'], operations=final_operations)
