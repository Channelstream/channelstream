import pytest
from pyramid import testing
import channelstream.channel
import channelstream.connection
import channelstream.user


class BaseInternalsTest(object):
    def setup_method(self, method):
        channelstream.channel.CHANNELS = []
        channelstream.connection.CONNECTIONS = []
        channelstream.user.USERS = []
        self.CHANNELS = channelstream.channel.CHANNELS
        self.CONNECTIONS = channelstream.connection.CONNECTIONS
        self.USERS = channelstream.user.USERS


class TestChannel(BaseInternalsTest):
    def test_create_defaults(self):
        channel = channelstream.channel.Channel('test', long_name='long name')
        assert channel.name == 'test'
        assert channel.long_name == 'long name'
        assert channel.connections == {}
        assert channel.notify_presence is False
        assert channel.broadcast_presence_with_user_lists is False
        assert channel.salvageable is False
        assert channel.store_history is False
        assert channel.history_size == 10
        assert channel.history == []

    @pytest.mark.parametrize('prop, value', [
        ('notify_presence', True),
        ('store_history', 6),
        ('history_size', 42),
        ('broadcast_presence_with_user_lists', True)
    ])
    def test_create_set_config(self, prop, value):
        channel_configs = {'test': {prop: value}}
        channel = channelstream.channel.Channel('test',
                                                channel_configs=channel_configs)
        assert getattr(channel, prop) == value

    def test_create_set_config_diff_name(self):
        channel_configs = {'test2': {'notify_presence': True}}
        channel = channelstream.channel.Channel('test',
                                                channel_configs=channel_configs)
        assert channel.notify_presence is False

    def test_add_connection(self):
        connection = channelstream.connection.Connection('test_user',
                                                         conn_id='A')
        channel = channelstream.channel.Channel('test')
        channel.add_connection(connection)
        assert len(channel.connections) == 1
        assert 'test_user' in channel.connections
        assert connection in channel.connections['test_user']


def dummy_request():
    return testing.DummyRequest()


class BaseViewTest(BaseInternalsTest):
    def setup(self):
        self.config = testing.setUp(settings={})
        self.settings = self.config.get_settings()


class TestConnectViews(BaseViewTest):
    def setup(self):
        super(TestConnectViews, self).setup()
        from .wsgi_views.server import ServerViews
        self.view_cls = ServerViews(dummy_request())

    def test_connect(self):
        result = self.view_cls.connect()
        print result
        assert 1 == 2


class TestStubState(BaseViewTest):
    def test_subscribe(self):
        pass

    def test_unsubscribe(self):
        pass

    def test__add_CORS(self):
        pass

    def test_handle_CORS(self):
        pass

    def test_message(self):
        pass

    def test_disconnect(self):
        pass

    def test_channel_config(self):
        pass

    def test_admin(self):
        pass

    def test_info(self):
        pass
