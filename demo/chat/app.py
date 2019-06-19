from gevent import monkey

monkey.patch_all()

import argparse
import os
from gevent.pywsgi import WSGIServer
from pyramid.config import Configurator
from pyramid.events import NewRequest


def main():
    demo_path = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(description="Run demo.")
    parser.add_argument("--demo-port", default=6543, type=int, help="Demo app port")
    parser.add_argument(
        "--channelstream-url",
        default="http://127.0.0.1:8000",
        help="Channelstream API URL",
    )
    parser.add_argument(
        "--channelstream-ws-url",
        default="http://127.0.0.1:8000/ws",
        help="Channelstream Websocket URL",
    )
    parser.add_argument(
        "--channelstream-secret", default="secret", help="Channelstream secret"
    )
    parser.add_argument(
        "--channelstream-admin-secret",
        default="admin_secret",
        help="Channelstream admin secret",
    )

    args = parser.parse_args()

    with Configurator() as config:
        config.include("pyramid_jinja2")
        # small hack to get non-registered app working
        config.add_static_view(name="static", path="__main__:static")
        # set up channelstream config
        config.registry.settings["channelstream_url"] = args.channelstream_url
        config.registry.settings["channelstream_ws_url"] = args.channelstream_ws_url
        config.registry.settings["secret"] = args.channelstream_secret
        config.registry.settings["admin_secret"] = args.channelstream_admin_secret

        # our routes
        config.add_route("/", "/")
        config.add_route("section_action", "/{section}/{action}")
        config.add_route(
            "api_listen", "{url}/listen".format(url=args.channelstream_url)
        )
        config.add_route("api_listen_ws", args.channelstream_ws_url)
        config.add_route(
            "api_disconnect", "{url}/disconnect".format(url=args.channelstream_url)
        )
        # gevent wsgi server doesn't set scheme based on proxy settings
        def new_request_sub(event):
            environ = event.request.environ
            if (
                environ.get("HTTP_X_FORWARDED_PROTO") == "https"
                or environ.get("HTTP_X_FORWARDED_SSL") == "on"
            ):
                environ["wsgi.url_scheme"] = "https"

        config.add_subscriber(new_request_sub, NewRequest)
        config.scan("views")
        app = config.make_wsgi_app()

    server = WSGIServer(("0.0.0.0", args.demo_port), app)
    print(
        "Assuming Channelstream server is runnng on {url}".format(
            url=args.channelstream_url
        )
    )
    print("The demo is assuming DEFAULT secret variables")
    print("visit demo at http://127.0.0.1:{port}/".format(port=args.demo_port))
    server.serve_forever()


if __name__ == "__main__":
    main()
