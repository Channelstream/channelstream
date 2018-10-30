from gevent import monkey

monkey.patch_all()

import os
from gevent.pywsgi import WSGIServer
from pyramid.config import Configurator


def main():
    demo_path = os.path.dirname(os.path.abspath(__file__))

    with Configurator() as config:
        config.include("pyramid_jinja2")
        # small hack to get non-registered app working
        config.add_static_view(name="static", path="__main__:static")
        # set up channelstream config
        # hardcoded for now
        host = "127.0.0.1"
        port = 8000
        secret = "secret"
        admin_secret = "admin_secret"
        config.registry.settings["host"] = host
        config.registry.settings["port"] = port
        config.registry.settings["secret"] = secret
        config.registry.settings["admin_secret"] = admin_secret

        # our routes
        config.add_route("/", "/")
        config.add_route("section_action", "/{section}/{action}")
        config.add_route(
            "api_listen", "http://{host}:{port}/listen".format(host=host, port=port)
        )
        config.add_route(
            "api_listen_ws", "http://{host}:{port}/ws".format(host=host, port=port)
        )
        config.add_route(
            "api_disconnect",
            "http://{host}:{port}/disconnect".format(host=host, port=port),
        )
        print(os.path.join(demo_path, "static"))

        config.scan("views")
        app = config.make_wsgi_app()

    server = WSGIServer(("0.0.0.0", 6543), app)
    print(
        "Assuming Channelstream server is runnng on http://{host}:{port}".format(
            host=host, port=port
        )
    )
    print("The demo is assuming DEFAULT secret variables")
    print("visit demo at http://127.0.0.1:6543/")
    server.serve_forever()


if __name__ == "__main__":
    main()
