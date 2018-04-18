import functools
from apispec import APISpec, utils


def add_pyramid_paths(
        spec, route_name, request=None, request_method=None, **kwargs):
    """
    :param spec:
    :param route_name:
    :param request:
    :param request_method:
    :param kwargs:
    :return:

    Adds a route and view info to spec

    """
    from pyramid.threadlocal import get_current_request
    if request is None:
        request = get_current_request()

    registry = request.registry
    introspector = registry.introspector
    route = introspector.get('routes', route_name)
    views = introspector.related(route)
    if request_method:
        kwargs['request_methods'] = request_method
        kwargs.setdefault('route_name', route_name)

    for view in views:
        matches = True
        for kw in kwargs.keys():
            if not view.get(kw) == kwargs[kw]:
                matches = False

        if not matches:
            continue

        if view.get('attr'):
            f_view = getattr(view['callable'], view['attr'])
        else:
            f_view = view.get('callable')

        operations = utils.load_operations_from_docstring(f_view.__doc__)
        spec.add_path(route['pattern'], operations=operations)
