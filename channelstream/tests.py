import pytest
from datetime import datetime, timedelta

from gevent.queue import Queue, Empty
from pyramid import testing

import channelstream
from channelstream.channel import Channel
from channelstream.connection import Connection
from channelstream.user import User


class BaseInternalsTest(object):
    def setup_method(self, method):
        channelstream.CHANNELS = {}
        channelstream.CONNECTIONS = {}
        channelstream.USERS = {}


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

    def test_remove_non_existant_connection(self):
        channel = Channel('test')
        connection = Connection('test_user', conn_id='A')
        channel.remove_connection(connection)
        assert len(channel.connections['test_user']) == 0

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

    def test_presence_message(self):
        user = User('test_user')
        connection = Connection('test_user', conn_id='A')
        user.add_connection(connection)
        channel = Channel('test')
        channel.add_connection(connection)
        payload = channel.send_notify_presence_info('test_user', 'join')
        assert payload['user'] == 'test_user'
        assert payload['message']['action'] == 'join'
        assert payload['type'] == 'presence'
        assert payload['channel'] == 'test'
        assert len(payload['users']) == 0

    def test_presence_message_w_users(self):
        user = User('test_user')
        user.state_from_dict({'key': '1', 'key2': '2'})
        user.state_public_keys = ['key2']
        channelstream.USERS[user.username] = user
        connection = Connection('test_user', conn_id='A')
        user.add_connection(connection)
        user2 = User('test_user2')
        user2.state_from_dict({'key': '1', 'key2': '2'})
        channelstream.USERS[user2.username] = user2
        connection2 = Connection('test_user2', conn_id='A')
        user2.add_connection(connection2)
        config = {'test': {'notify_presence': True,
                           'broadcast_presence_with_user_lists': True}}
        channel = Channel('test', channel_configs=config)
        channel.add_connection(connection)
        channel.add_connection(connection2)
        payload = channel.send_notify_presence_info('test_user', 'join')
        assert len(payload['users']) == 2
        sorted_users = sorted(payload['users'], key=lambda x: x['user'])
        assert sorted_users == [
            {'state': {'key2': '2'}, 'user': 'test_user'},
            {'state': {}, 'user': 'test_user2'}
        ]


class TestConnection(BaseInternalsTest):
    def test_create_defaults(self):
        now = datetime.utcnow()
        connection = Connection('test', 'X')
        assert connection.username == 'test'
        assert now <= connection.last_active
        assert connection.socket is None
        assert connection.queue is None
        assert connection.id == 'X'

    def test_mark_for_gc(self):
        long_time_ago = datetime.utcnow() - timedelta(days=50)
        connection = Connection('test', 'X')
        connection.mark_for_gc()
        assert connection.last_active < long_time_ago

    def test_message(self):
        connection = Connection('test', 'X')
        connection.queue = Queue()
        connection.add_message('test')
        assert connection.queue.get() == ['test']

    def test_heartbeat(self):
        connection = Connection('test', 'X')
        connection.queue = Queue()
        connection.heartbeat()
        assert connection.queue.get() == []

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

        # def test_connect(self):
        #     result = self.view_cls.connect()
        #     print result
        #     assert 1 == 2


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
