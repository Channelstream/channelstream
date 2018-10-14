from gevent import monkey

monkey.patch_all()

import uuid
import pytest
import mock
from datetime import datetime
from pyramid import testing
from channelstream.server_state import get_state


@pytest.fixture
def test_uuids():
    return [
        uuid.UUID("12345678-1234-5678-1234-567812345678"),
        uuid.UUID("22345678-1234-5678-1234-567812345678"),
        uuid.UUID("32345678-1234-5678-1234-567812345678"),
        uuid.UUID("42345678-1234-5678-1234-567812345678"),
        uuid.UUID("52345678-1234-5678-1234-567812345678"),
        uuid.UUID("62345678-1234-5678-1234-567812345678"),
        uuid.UUID("72345678-1234-5678-1234-567812345678"),
        uuid.UUID("82345678-1234-5678-1234-567812345678"),
        uuid.UUID("92345678-1234-5678-1234-567812345678"),
    ]


@pytest.fixture
def cleanup_globals():
    server_state = get_state()
    server_state.channels = {}
    server_state.connections = {}
    server_state.users = {}
    server_state.stats = {
        "total_messages": 0,
        "total_unique_messages": 0,
        "started_on": datetime.utcnow(),
    }


@pytest.fixture
def pyramid_config():
    # from pyramid.request import Request
    # request = Request.blank('/', base_url='http://foo.com')
    config = testing.setUp(settings={})
    settings = config.get_settings()
    return config, settings


@pytest.fixture
def dummy_request():
    app_request = testing.DummyRequest()
    app_request.handle_cors = mock.Mock()
    return app_request
