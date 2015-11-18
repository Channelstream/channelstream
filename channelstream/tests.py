import pytest
from pyramid import testing
import channelstream
from  channelstream.channel import Channel
from channelstream.connection import Connection
from channelstream.user import User


class BaseInternalsTest(object):
    def setup_method(self, method):
        channelstream.CHANNELS = {}
        channelstream.CONNECTIONS = {}
        channelstream.USERS = {}
        self.CHANNELS = channelstream.CHANNELS
        self.CONNECTIONS = channelstream.CONNECTIONS
        self.USERS = channelstream.USERS


class TestChannel(BaseInternalsTest):
    def test_create_defaults(self):
        channel = Channel('test', long_name='long name')
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
        channel = Channel('test', channel_configs=channel_configs)

        assert getattr(channel, prop) == value

    def test_create_set_config_diff_name(self):
        channel_configs = {'test2': {'notify_presence': True}}
        channel = Channel('test', channel_configs=channel_configs)
        assert channel.notify_presence is False

    def test_add_connection(self):
        connection = Connection('test_user',
                                conn_id='A')
        channel = Channel('test')
        channel.add_connection(connection)
        assert len(channel.connections['test_user']) == 1
        assert 'test_user' in channel.connections
        assert connection in channel.connections['test_user']

    def test_remove_connection(self):
        connection = Connection('test_user', conn_id='A')
        connection2 = Connection('test_user2', conn_id='B')
        connection3 = Connection('test_user', conn_id='C')
        channel = Channel('test')
        channel.add_connection(connection)
        channel.add_connection(connection2)
        channel.remove_connection(connection)
        assert len(channel.connections['test_user']) == 0
        assert len(channel.connections['test_user2']) == 1
        channel.add_connection(connection)
        channel.add_connection(connection3)
        channel.remove_connection(connection)
        assert len(channel.connections['test_user']) == 1

    def test_add_connection_w_presence(self):
        user = User('test_user')
        channelstream.USERS[user.username] = user
        connection = Connection('test_user', conn_id='A')
        user.add_connection(connection)
        config = {'test': {'notify_presence': True,
                           'broadcast_presence_with_user_lists': True}}
        channel = Channel('test', channel_configs=config)
        channel.add_connection(connection)
        assert len(channel.connections['test_user']) == 1
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
