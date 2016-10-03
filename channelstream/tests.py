from gevent import monkey

monkey.patch_all()

import pytest
import mock
from datetime import datetime, timedelta
from gevent.queue import Queue, Empty
from pyramid import testing
import channelstream
import channelstream.gc
from channelstream.channel import Channel
from channelstream.connection import Connection
from channelstream.user import User


@pytest.fixture
def cleanup_globals():
    channelstream.CHANNELS = {}
    channelstream.CONNECTIONS = {}
    channelstream.USERS = {}


@pytest.mark.usefixtures("cleanup_globals")
class TestChannel(object):
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

    def test_repr(self):
        channel = Channel('test', long_name='long name')
        assert repr(channel) == '<Channel: test, connections:0>'

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
        assert repr(channel) == '<Channel: test, connections:1>'

    def test_remove_connection(self):
        connection = Connection('test_user', conn_id='A')
        connection2 = Connection('test_user2', conn_id='B')
        connection3 = Connection('test_user', conn_id='C')
        channel = Channel('test')
        channel.add_connection(connection)
        channel.add_connection(connection2)
        channel.remove_connection(connection)
        assert 'test_user' not in channel.connections
        assert len(channel.connections['test_user2']) == 1
        channel.add_connection(connection)
        channel.add_connection(connection3)
        channel.remove_connection(connection)
        assert len(channel.connections['test_user']) == 1

    def test_remove_non_existant_connection(self):
        channel = Channel('test')
        connection = Connection('test_user', conn_id='A')
        channel.remove_connection(connection)
        assert 'test_user' not in channel.connections

    def test_remove_connection_w_presence(self):
        user = User('test_user')
        channelstream.USERS[user.username] = user
        connection = Connection('test_user', conn_id='A')
        user.add_connection(connection)
        config = {'test': {'notify_presence': True,
                           'broadcast_presence_with_user_lists': True}}
        channel = Channel('test', channel_configs=config)
        channel.add_connection(connection)
        channel.remove_connection(connection)

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

    def test_history(self):
        config = {'test': {'store_history': True,
                           'history_size': 3}}
        channel = Channel('test', long_name='long name',
                          channel_configs=config)
        channel.add_message({'message': 'test1', 'type': 'message'})
        channel.add_message({'message': 'test2', 'type': 'message'})
        channel.add_message({'message': 'test3', 'type': 'message'})
        channel.add_message({'message': 'test4', 'type': 'message'})

        assert len(channel.history) == 3
        assert channel.history == [
            {'channel': 'test', 'message': 'test2', 'type': 'message'},
            {'channel': 'test', 'message': 'test3', 'type': 'message'},
            {'channel': 'test', 'message': 'test4', 'type': 'message'}
        ]

    def test_user_state(self):
        user = User('test_user')
        changed = user.state_from_dict({'key': '1', 'key2': '2'})
        user.state_public_keys = ['key2']
        connection = Connection('test_user', conn_id='A')
        user.add_connection(connection)
        channel = Channel('test')
        channel.add_connection(connection)
        payload = channel.send_user_state(user, changed)
        assert payload['user'] == 'test_user'
        assert payload['message']['state'] == {'key2': '2'}
        assert payload['message']['changed'] == [{'key': 'key2', 'value': '2'}]
        assert payload['type'] == 'user_state_change'
        assert payload['channel'] == 'test'

    def test_user_single_assignment(self):
        user = User('test_user')
        connection = Connection('test_user', conn_id='A')
        user.add_connection(connection)
        channel = Channel('test')
        channel.add_connection(connection)
        [channel] == user.get_channels()

    def test_user_multi_assignment(self):
        user = User('test_user')
        connection = Connection('test_user', conn_id='A')
        connection2 = Connection('test_user', conn_id='A2')
        connection3 = Connection('test_user', conn_id='A3')
        user.add_connection(connection)
        user.add_connection(connection2)
        user.add_connection(connection3)
        channel = Channel('test')
        channel2 = Channel('test2')
        channelstream.CHANNELS[channel.name] = channel
        channelstream.CHANNELS[channel2.name] = channel2
        channel.add_connection(connection)
        channel.add_connection(connection2)
        channel2.add_connection(connection3)
        assert ['test', 'test2'] == sorted([c.name for c in user.get_channels()])


@pytest.mark.usefixtures("cleanup_globals")
class TestConnection(object):
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
        connection.add_message({'message': 'test'})
        assert connection.queue.get() == [{'message': 'test'}]

    def test_heartbeat(self):
        connection = Connection('test', 'X')
        connection.queue = Queue()
        connection.heartbeat()
        assert connection.queue.get() == []


class TestUser(object):
    def test_create_defaults(self):
        user = User('test_user')
        user.state_from_dict({'key': '1', 'key2': '2'})
        user.state_public_keys = ['key2']
        assert repr(user) == '<User:test_user, connections:0>'
        assert sorted(user.state.items()) == sorted({'key': '1',
                                                     'key2': '2'}.items())
        assert user.public_state == {'key2': '2'}

    def test_messages(self):
        user = User('test_user')
        connection = Connection('test_user', conn_id='A')
        connection.queue = Queue()
        connection2 = Connection('test_user', conn_id='B')
        connection2.queue = Queue()
        user.add_connection(connection)
        user.add_connection(connection2)
        user.add_message({'type': 'message'})
        assert len(user.connections) == 2
        assert len(user.connections[0].queue.get()) == 1
        assert len(user.connections[1].queue.get()) == 1


@pytest.mark.usefixtures("cleanup_globals")
class TestGC(object):
    def test_gc_connections_active(self):
        channel = Channel('test')
        channelstream.CHANNELS[channel.name] = channel
        channel2 = Channel('test2')
        channelstream.CHANNELS[channel2.name] = channel2
        user = User('test_user')
        channelstream.USERS[user.username] = user
        user2 = User('test_user2')
        channelstream.USERS[user2.username] = user2
        connection = Connection('test_user', '1')
        channelstream.CONNECTIONS[connection.id] = connection
        connection2 = Connection('test_user', '2')
        channelstream.CONNECTIONS[connection2.id] = connection2
        connection3 = Connection('test_user2', '3')
        channelstream.CONNECTIONS[connection3.id] = connection3
        connection4 = Connection('test_user2', '4')
        channelstream.CONNECTIONS[connection4.id] = connection4
        user.add_connection(connection)
        user.add_connection(connection2)
        channel.add_connection(connection)
        channel.add_connection(connection2)
        user2.add_connection(connection3)
        user2.add_connection(connection4)
        channel2.add_connection(connection3)
        channel2.add_connection(connection4)
        channelstream.gc.gc_conns()
        conns = channelstream.CHANNELS['test'].connections['test_user']
        assert len(conns) == 2
        assert len(channelstream.CONNECTIONS.items()) == 4
        conns = channelstream.CHANNELS['test2'].connections['test_user2']
        assert len(conns) == 2
        assert len(user.connections) == 2
        assert len(user2.connections) == 2
        assert sorted(channel.connections.keys()) == ['test_user']
        assert sorted(channel2.connections.keys()) == ['test_user2']

    def test_gc_connections_collecting(self):
        channel = Channel('test')
        channelstream.CHANNELS[channel.name] = channel
        channel2 = Channel('test2')
        channelstream.CHANNELS[channel2.name] = channel2
        user = User('test_user')
        channelstream.USERS[user.username] = user
        user2 = User('test_user2')
        channelstream.USERS[user2.username] = user2
        connection = Connection('test_user', '1')
        channelstream.CONNECTIONS[connection.id] = connection
        connection2 = Connection('test_user', '2')
        connection2.mark_for_gc()
        channelstream.CONNECTIONS[connection2.id] = connection2
        connection3 = Connection('test_user2', '3')
        connection3.mark_for_gc()
        channelstream.CONNECTIONS[connection3.id] = connection3
        connection4 = Connection('test_user2', '4')
        channelstream.CONNECTIONS[connection4.id] = connection4
        user.add_connection(connection)
        user.add_connection(connection2)
        channel.add_connection(connection)
        channel.add_connection(connection2)
        user2.add_connection(connection3)
        user2.add_connection(connection4)
        channel2.add_connection(connection3)
        channel2.add_connection(connection4)
        channelstream.gc.gc_conns()
        assert len(channelstream.CONNECTIONS.items()) == 2
        conns = channelstream.CHANNELS['test'].connections['test_user']
        assert len(conns) == 1
        assert conns == [connection]
        conns = channelstream.CHANNELS['test2'].connections['test_user2']
        assert len(conns) == 1
        assert conns == [connection4]
        assert len(user.connections) == 1
        assert len(user2.connections) == 1
        connection.mark_for_gc()
        connection4.mark_for_gc()
        channelstream.gc.gc_conns()
        assert 'test_user' not in channelstream.CHANNELS['test'].connections
        assert 'test_user2' not in channelstream.CHANNELS['test2'].connections
        assert len(channelstream.CHANNELS['test'].connections.items()) == 0
        assert len(channelstream.CHANNELS['test2'].connections.items()) == 0

    def test_users_active(self):
        user = User('test_user')
        channelstream.USERS[user.username] = user
        user2 = User('test_user2')
        channelstream.USERS[user2.username] = user2
        channelstream.gc.gc_users()
        assert len(channelstream.USERS.items()) == 2
        user.last_active -= timedelta(days=2)
        channelstream.gc.gc_users()
        assert len(channelstream.USERS.items()) == 1


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


@pytest.mark.usefixtures('cleanup_globals', 'pyramid_config')
class TestConnectViews(object):
    def test_bad_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {}
        view_cls = ServerViews(dummy_request)
        result = view_cls.connect()
        assert result == {'error': 'No username specified'}

    def test_good_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {'username': 'username',
                                   'conn_id': 'X',
                                   'fresh_user_state': {'key': 'foo'},
                                   'user_state': {'bar': 'baz'},
                                   'state_public_keys': 'bar',
                                   'channels': ['a', 'aB'],
                                   'channel_configs': {
                                       'a': {'store_history': True,
                                             'history_size': 2}}}
        view_cls = ServerViews(dummy_request)
        assert channelstream.CHANNELS == {}
        result = view_cls.connect()
        assert len(channelstream.CHANNELS.keys()) == 2
        assert 'username' in channelstream.USERS
        assert 'X' in channelstream.CONNECTIONS
        assert result['channels'] == ['a', 'aB']
        assert result['state'] == {'bar': 'baz', 'key': 'foo'}
        assert result['conn_id'] == 'X'
        channels_info = result['channels_info']['channels']
        assert len(channels_info.keys()) == 2
        assert channels_info['a']['total_users'] == 1
        assert channels_info['a']['total_connections'] == 1
        assert channels_info['a']['users'] == ['username']
        assert channels_info['a']['history'] == []
        assert result['channels_info']['users'] == [
            {'state': {'bar': 'baz', 'key': 'foo'}, 'user': 'username'}
        ]

@pytest.mark.usefixtures('cleanup_globals', 'pyramid_config')
class TestUserStateViews(object):
    def test_bad_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {}
        view_cls = ServerViews(dummy_request)
        result = view_cls.user_state()
        assert result == {'error': 'No username specified'}

    def test_not_found_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {'user': 'blabla'}
        view_cls = ServerViews(dummy_request)
        result = view_cls.user_state()
        assert result == {'error': 'User not found'}

    def test_good_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {'username': 'test',
                                   'conn_id': 'x',
                                   'fresh_user_state': {'key': 'foo'},
                                   'user_state': {'bar': 'baz'},
                                   'state_public_keys': 'bar',
                                   'channels': ['a', 'aB'],
                                   'channel_configs': {
                                       'a': {'store_history': True,
                                             'history_size': 2}}}
        view_cls = ServerViews(dummy_request)
        view_cls.connect()
        dummy_request.json_body = {
            "user": 'test',
            "user_state": {"bar": 2, 'private': 'im_private'},
            "state_public_keys": ["avatar", "bar"]
        }
        view_cls = ServerViews(dummy_request)
        result = view_cls.user_state()
        sorted_keys = sorted(['bar', 'key', 'private'])
        assert sorted_keys == sorted(result['user_state'].keys())
        assert result['user_state']['private'] == 'im_private'
        sorted_changed = sorted([x['key'] for x in result['changed_state']])
        assert sorted_changed == sorted(['bar', 'private'])

@pytest.mark.usefixtures('cleanup_globals', 'pyramid_config')
class TestSubscribeViews(object):
    def test_bad_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {}
        view_cls = ServerViews(dummy_request)
        result = view_cls.subscribe()
        assert result == {'error': 'Unknown connection'}

    def test_good_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {'username': 'test',
                                   'conn_id': 'x',
                                   'fresh_user_state': {'key': 'foo'},
                                   'user_state': {'bar': 'baz'},
                                   'state_public_keys': 'bar',
                                   'channels': ['a', 'aB'],
                                   'channel_configs': {
                                       'a': {'store_history': True,
                                             'history_size': 2}}}
        view_cls = ServerViews(dummy_request)
        view_cls.connect()
        dummy_request.json_body = {"conn_id": 'x',
                                   "channels": ['b'],
                                   "channel_configs": {
                                       "a": {"notify_presence": True},
                                       "b": {"notify_presence": True}}
                                   }
        view_cls = ServerViews(dummy_request)
        result = view_cls.subscribe()
        assert sorted(result['channels']) == sorted(['a', 'aB', 'b'])
        assert result['channels_info']['users'] == [
            {'state': {'bar': 'baz', 'key': 'foo'}, 'user': 'test'}]
        assert 'a' in result['channels_info']['channels']
        assert 'b' in result['channels_info']['channels']
        assert result['channels_info']['channels']['a'][
                   'total_connections'] == 1
        assert result['channels_info']['channels']['a']['total_users'] == 1
        assert result['channels_info']['channels']['a']['history'] == []
        assert result['channels_info']['channels']['a']['users'] == ['test']


@pytest.mark.usefixtures('cleanup_globals', 'pyramid_config')
class TestUnsubscribeViews(object):
    def test_bad_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {}
        view_cls = ServerViews(dummy_request)
        result = view_cls.unsubscribe()
        assert result == {'error': 'Unknown connection'}

    def test_good_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {'username': 'test',
                                   'conn_id': 'x',
                                   'fresh_user_state': {'key': 'foo'},
                                   'user_state': {'bar': 'baz'},
                                   'state_public_keys': 'bar',
                                   'channels': ['a', 'aB', 'aC'],
                                   'channel_configs': {
                                       'a': {'store_history': True,
                                             'history_size': 2}}}
        view_cls = ServerViews(dummy_request)
        view_cls.connect()
        dummy_request.json_body = {"conn_id": 'x',
                                   "channels": ['aC', 'a']
                                   }
        view_cls = ServerViews(dummy_request)
        result = view_cls.unsubscribe()
        assert sorted(result['channels']) == sorted(['aB'])

    def test_non_existing_channel(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {'username': 'test',
                                   'conn_id': 'x',
                                   'fresh_user_state': {'key': 'foo'},
                                   'user_state': {'bar': 'baz'},
                                   'state_public_keys': 'bar',
                                   'channels': ['a', 'aB', 'aC'],
                                   'channel_configs': {
                                       'a': {'store_history': True,
                                             'history_size': 2}}}
        view_cls = ServerViews(dummy_request)
        view_cls.connect()
        dummy_request.json_body = {"conn_id": 'x',
                                   "channels": ['d']
                                   }
        view_cls = ServerViews(dummy_request)
        result = view_cls.unsubscribe()
        assert sorted(result['channels']) == sorted(['a', 'aB', 'aC'])


@pytest.mark.usefixtures('cleanup_globals', 'pyramid_config')
class TestInfoView(object):
    def test_empty_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {}
        view_cls = ServerViews(dummy_request)
        result = view_cls.info()
        assert result['channels'] == {}
        assert result['users'] == []

    def test_subscribed_json(self, dummy_request):
        from channelstream.wsgi_views.server import ServerViews
        dummy_request.json_body = {'username': 'test1',
                                   'conn_id': 'x',
                                   'fresh_user_state': {'key': 'foo'},
                                   'user_state': {'bar': 'baz'},
                                   'state_public_keys': 'bar',
                                   'channels': ['a', 'aB'],
                                   'channel_configs': {
                                       'a': {'store_history': True,
                                             'history_size': 2}}}
        view_cls = ServerViews(dummy_request)
        view_cls.connect()
        dummy_request.json_body = {'username': 'test2',
                                   'conn_id': 'y',
                                   'fresh_user_state': {'key': 'foo1'},
                                   'user_state': {'bar': 'baz1'},
                                   'state_public_keys': 'key',
                                   'channels': ['a', 'c'],
                                   'channel_configs': {
                                       'c': {'store_history': True,
                                             'history_size': 2}}}
        view_cls = ServerViews(dummy_request)
        view_cls.connect()
        result = view_cls.info()
        assert sorted(('a', 'aB', 'c')) == sorted(result['channels'].keys())
        assert result['users']
        compA = sorted(result['channels']['a']['users'])
        compB = sorted(['test1', 'test2'])
        assert compA == compB
        assert result['channels']['a']['total_users'] == 2
        assert result['channels']['a']['total_connections'] == 2
        assert result['channels']['c']['users'] == ['test2']
        assert result['channels']['c']['total_users'] == 1
        assert result['channels']['c']['total_connections'] == 1
        assert result['channels']['aB']['users'] == ['test1']
        compA = sorted(result['users'],
                       key=lambda x: x['user'])
        compB = sorted([
            {'state': {'bar': 'baz', 'key': 'foo'}, 'user': 'test1'},
            {'state': {'bar': 'baz1', 'key': 'foo1'}, 'user': 'test2'}],
            key=lambda x: x['user'])
        assert compA == compB
        dummy_request.body = 'NOTEMPTY'
        dummy_request.json_body = {'info': {'channels': ['a']}}
        view_cls = ServerViews(dummy_request)
        result = view_cls.info()
        assert 'a' in result['channels']
        assert 'aB' not in result['channels']
