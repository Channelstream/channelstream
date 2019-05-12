from gevent import monkey

monkey.patch_all()

import copy
import pytest

from webtest import TestApp
from channelstream.cli import SHARED_DEFAULTS
from channelstream.cli.start import RoutingApplication


@pytest.mark.usefixtures("cleanup_globals")
class TestServerConfigView(object):
    def test_defaults(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        application = RoutingApplication(config)
        app = TestApp(application, extra_environ={"REMOTE_ADDR": "127.0.0.1"})
        app.get("/", status=404)
        app.post("/connect", status=403)

    def test_enforce_https_wrong(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        config["enforce_https"] = True
        application = RoutingApplication(config)
        app = TestApp(application, extra_environ={"REMOTE_ADDR": "127.0.0.1"})
        app.get("/", status=406)
        app.post("/connect", status=406)

    def test_enforce_https_proper(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        config["enforce_https"] = True
        application = RoutingApplication(config)
        app = TestApp(
            application,
            extra_environ={"REMOTE_ADDR": "127.0.0.1", "wsgi.url_scheme": "https"},
        )
        app.get("/", status=404)
        app.post("/connect", status=403)
