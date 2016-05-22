import logging
import uuid
from datetime import datetime
import gevent
import six
from gevent.queue import Queue, Empty
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import forget
import channelstream
from channelstream.user import User
from channelstream.connection import Connection
from channelstream.channel import Channel
from ..ext_json import json

log = logging.getLogger(__name__)


def pass_message(msg, stats):
    if msg.get('timestamp'):
        # if present lets use timestamp provided in the message
        if '.' in msg['timestamp']:
            timestmp = datetime.strptime(msg['timestamp'],
                                         '%Y-%m-%dT%H:%M:%S.%f')
        else:
            timestmp = datetime.strptime(msg['timestamp'],
                                         '%Y-%m-%dT%H:%M:%S')
    else:
        timestmp = datetime.utcnow()
    message = {'uuid': str(uuid.uuid4()).replace('-', ''),
               'user': msg.get('user'),
               'message': msg['message'],
               'type': 'message',
               'timestamp': timestmp}
    pm_users = msg.get('pm_users', [])
    total_sent = 0
    stats['total_unique_messages'] += 1
    if msg.get('channel'):
        channel_inst = channelstream.CHANNELS.get(msg['channel'])
        if channel_inst:
            total_sent += channel_inst.add_message(message,
                                                   pm_users=pm_users)
    elif pm_users:
        # if pm then iterate over all users and notify about new message!
        for username in pm_users:
            user_inst = channelstream.USERS.get(username)
            if user_inst:
                total_sent += user_inst.add_message(message)
    stats['total_messages'] += total_sent


def get_connection_channels(connection):
    found_channels = []
    for channel in six.itervalues(channelstream.CHANNELS):
        user_conns = channel.connections.get(connection.username) or []
        if connection in user_conns:
            found_channels.append(channel.name)
    return found_channels


class ServerViews(object):
    def __init__(self, request):
        self.request = request

    def _get_channel_info(self, req_channels=None, include_history=True,
                          include_connections=False, include_users=False,
                          exclude_channels=None):
        """
        Gets channel information for req_channels or all channels
        if req_channels is not present
        :param: include_history (bool) will include message history
                for the channel
        :param: include_connections (bool) will include connection list
                for the channel
        :param: include_users (bool) will include user list for the channel
        :param: exclude_channels (bool) will exclude specific channels
                from info list (handy to exclude global broadcast)
        """

        if not exclude_channels:
            exclude_channels = []
        start_time = datetime.utcnow()

        json_data = {"channels": {},
                     "unique_users": len(channelstream.USERS),
                     "users": []}

        users_to_list = []

        # select everything for empty list
        if not req_channels:
            channel_instances = six.itervalues(channelstream.CHANNELS)
        else:
            channel_instances = [channelstream.CHANNELS[c]
                                 for c in req_channels]

        for channel_inst in channel_instances:
            if channel_inst.name in exclude_channels:
                continue

            json_data["channels"][channel_inst.name] = {'history': []}
            chan_info = json_data["channels"][channel_inst.name]
            if include_history:
                chan_info['history'] = channel_inst.history
            chan_info['total_users'] = len(channel_inst.connections)
            chan_info['total_connections'] = sum(
                [len(conns) for conns in channel_inst.connections.values()])
            chan_info['users'] = []
            for username in channel_inst.connections.keys():
                user_inst = channelstream.USERS.get(username)
                if include_users and user_inst.username not in users_to_list:
                    users_to_list.append(user_inst.username)
                udata = {'user': user_inst.username,
                         "connections": []}
                if include_connections:
                    udata['connections'] = [conn.id for conn in
                                            channel_inst.connections[username]]
                chan_info['users'].append(udata)
            chan_info['last_active'] = channel_inst.last_active

        for username in users_to_list:
            json_data['users'].append(
                {'user': username,
                 'state': channelstream.USERS[username].state})
        log.info('info time: %s' % (datetime.utcnow() - start_time))
        return json_data

    def get_common_info(self, channels, info_config):
        include_history = info_config.get('include_history', True)
        include_users = info_config.get('include_users', True)
        exclude_channels = info_config.get('exclude_channels', [])
        include_connections = info_config.get('include_connections', False)
        channels_info = self._get_channel_info(
            channels, include_history=include_history,
            include_connections=include_connections,
            include_users=include_users, exclude_channels=exclude_channels)
        return channels_info

    @view_config(route_name='action', match_param='action=connect',
                 renderer='json', permission='access')
    def connect(self):
        """
        return the id of connected users - will be secured with password string
        for webapp to internally call the server - we combine conn string
        with user id, and we tell which channels the user is allowed to
        subscribe to
        """
        json_body = self.request.json_body
        username = json_body.get('username')
        fresh_user_state = json_body.get('fresh_user_state', {})
        update_user_state = json_body.get('user_state', {})
        channel_configs = json_body.get('channel_configs', {})
        state_public_keys = json_body.get('state_public_keys', None)
        conn_id = json_body.get('conn_id')
        subscribe_to_channels = json_body.get('channels')
        if username is None:
            self.request.response.status = 400
            return {'error': "No username specified"}
        if not subscribe_to_channels:
            self.request.response.status = 400
            return {'error': "No channels specified"}

        # everything is ok so lets add new connection to
        # channel and connection list
        with channelstream.lock:
            if username not in channelstream.USERS:
                user = User(username)
                user.state_from_dict(fresh_user_state)
                channelstream.USERS[username] = user
            else:
                user = channelstream.USERS[username]
            if state_public_keys is not None:
                user.state_public_keys = state_public_keys

            user.state_from_dict(update_user_state)
            connection = Connection(username, conn_id)
            if connection.id not in channelstream.CONNECTIONS:
                channelstream.CONNECTIONS[connection.id] = connection
            user.add_connection(connection)
            for channel_name in subscribe_to_channels:
                # user gets assigned to a channel
                if channel_name not in channelstream.CHANNELS:
                    channel = Channel(channel_name,
                                      channel_configs=channel_configs)
                    channelstream.CHANNELS[channel_name] = channel
                channelstream.CHANNELS[channel_name].add_connection(connection)
            log.info('connecting %s with uuid %s' % (username, connection.id))

        # get info config for channel information
        info_config = json_body.get('info') or {}
        channels_info = self.get_common_info(subscribe_to_channels,
                                             info_config)
        return {'conn_id': connection.id, 'state': user.state,
                'channels': subscribe_to_channels,
                'channels_info': channels_info}

    @view_config(route_name='action', match_param='action=subscribe',
                 renderer='json', permission='access')
    def subscribe(self, *args):
        """ call this to subscribe specific connection to new channels """
        json_body = self.request.json_body
        conn_id = json_body.get('conn_id', self.request.GET.get('conn_id'))
        connection = channelstream.CONNECTIONS.get(conn_id)
        subscribe_to_channels = json_body.get('channels')
        channel_configs = json_body.get('channel_configs', {})
        if not connection:
            self.request.response.status = 403
            return {'error': "Unknown connection"}
        if not subscribe_to_channels:
            self.request.response.status = 400
            return {'error': "No channels specified"}
        # everything is ok so lets add new connection to channel
        # and connection list
        # lets lock it just in case
        # find the right user
        user = channelstream.USERS.get(connection.username)
        with channelstream.lock:
            if user:
                for channel_name in subscribe_to_channels:
                    if channel_name not in channelstream.CHANNELS:
                        channel = Channel(channel_name,
                                          channel_configs=channel_configs)
                        channelstream.CHANNELS[channel_name] = channel
                    channelstream.CHANNELS[channel_name].add_connection(
                        connection)

        # get info config for channel information
        current_channels = get_connection_channels(connection)
        info_config = json_body.get('info') or {}
        channels_info = self.get_common_info(current_channels, info_config)
        return {"channels": current_channels,
                "channels_info": channels_info}

    @view_config(route_name='action', match_param='action=unsubscribe',
                 renderer='json', permission='access')
    def unsubscribe(self, *args):
        """ call this to unsubscribe specific connection from channels """
        json_body = self.request.json_body
        conn_id = json_body.get('conn_id', self.request.GET.get('conn_id'))
        connection = channelstream.CONNECTIONS.get(conn_id)
        unsubscribe_channels = json_body.get('channels')
        if not connection:
            self.request.response.status = 403
            return {'error': "Unknown connection"}
        if not unsubscribe_channels:
            self.request.response.status = 400
            return {'error': "No channels specified"}
        # everything is ok so lets add new connection to channel
        # and connection list
        # lets lock it just in case
        # find the right user
        user = channelstream.USERS.get(connection.username)
        with channelstream.lock:
            if user:
                for channel_name in unsubscribe_channels:
                    channelstream.CHANNELS[channel_name].remove_connection(
                        connection)

        # get info config for channel information
        current_channels = get_connection_channels(connection)
        info_config = json_body.get('info') or {}
        channels_info = self.get_common_info(current_channels, info_config)

        return {"channels": current_channels,
                "channels_info": channels_info}

    def _add_CORS(self):
        self.request.response.headers.add('Access-Control-Allow-Origin', '*')
        self.request.response.headers.add('XDomainRequestAllowed', '1')
        self.request.response.headers.add('Access-Control-Allow-Methods',
                                          'GET, POST, OPTIONS, PUT')
        self.request.response.headers.add('Access-Control-Allow-Headers',
                                          'Content-Type, Depth, User-Agent, '
                                          'X-File-Size, X-Requested-With, '
                                          'If-Modified-Since, X-File-Name, '
                                          'Cache-Control, Pragma, Origin, '
                                          'Connection, Referer, Cookie')
        self.request.response.headers.add('Access-Control-Max-Age', '86400')
        # self.request.response.headers.add('Access-Control-Allow-Credentials',
        #                                   'true')

    @view_config(route_name='action', match_param='action=listen',
                 request_method="OPTIONS", renderer='string')
    def handle_CORS(self):
        self._add_CORS()
        return ''

    @view_config(route_name='action', match_param='action=listen',
                 renderer='string')
    def listen(self):
        self._add_CORS()
        config = self.request.registry.settings
        self.conn_id = self.request.params.get('conn_id')
        connection = channelstream.CONNECTIONS.get(self.conn_id)
        if not connection:
            raise HTTPUnauthorized()
        # mark the conn active
        connection.last_active = datetime.utcnow()
        # attach a queue to connection
        connection.queue = Queue()

        def yield_response():
            # for chrome issues
            # yield ' ' * 1024
            # wait for this to wake up
            messages = []
            # block for first message - wake up after a while
            try:
                messages.extend(connection.queue.get(
                    timeout=config['wake_connections_after']))
            except Empty:
                pass
            # get more messages if enqueued takes up total 0.25s
            while True:
                try:
                    messages.extend(connection.queue.get(timeout=0.25))
                except Empty:
                    break
            cb = self.request.params.get('callback')
            if cb:
                yield cb + '(' + json.dumps(messages) + ')'
            else:
                yield json.dumps(messages)

        self.request.response.app_iter = yield_response()
        return self.request.response

    @view_config(route_name='action', match_param='action=user_state',
                 renderer='json', permission='access')
    def user_state(self):
        """ set the status of specific user """
        json_body = self.request.json_body
        username = json_body.get('user')
        user_state = json_body.get('user_state')
        state_public_keys = json_body.get('state_public_keys', None)
        if not username:
            self.request.response.status = 400
            return {'error': "No username specified"}

        user_inst = channelstream.USERS.get(username)
        if user_inst:
            user_inst.state_from_dict(user_state)
            if state_public_keys is not None:
                user_inst.state_public_keys = state_public_keys
            # mark active
            user_inst.last_active = datetime.utcnow()
        return user_inst.state

    @view_config(route_name='action', match_param='action=message',
                 renderer='json', permission='access')
    def message(self):
        msg_list = self.request.json_body
        for msg in msg_list:
            if not msg.get('channel') and not msg.get('pm_users', []):
                continue
            gevent.spawn(pass_message, msg, channelstream.stats)

    @view_config(route_name='action', match_param='action=disconnect',
                 renderer='json', permission='access')
    def disconnect(self):
        json_body = self.request.json_body
        conn_id = json_body.get('conn_id', self.request.GET.get('conn_id'))
        conn = channelstream.CONNECTIONS.get(conn_id)
        if conn is not None:
            conn.mark_for_gc()

    @view_config(route_name='action', match_param='action=channel_config',
                 renderer='json', permission='access')
    def channel_config(self):
        """ call this to reconfigure channels """
        json_body = self.request.json_body
        if not json_body:
            self.request.response.status = 400
            return {'error': "No channels specified"}

        with channelstream.lock:
            for channel_name, config in json_body.items():
                if not channelstream.CHANNELS.get(channel_name):
                    channel = Channel(channel_name,
                                      channel_configs=json_body)
                    channelstream.CHANNELS[channel_name] = channel
                else:
                    channel = channelstream.CHANNELS[channel_name]
                    channel.reconfigure_from_dict(json_body)
        channels_info = self._get_channel_info(json_body.keys(),
                                               include_history=False,
                                               include_users=False)
        return channels_info

    @view_config(
        context='channelstream.wsgi_views.wsgi_security:RequestBasicChallenge')
    def admin_challenge(self):
        response = HTTPUnauthorized()
        response.headers.update(forget(self.request))
        return response

    @view_config(route_name='admin',
                 renderer='templates/admin.jinja2', permission='access')
    def admin(self):
        uptime = datetime.utcnow() - channelstream.stats['started_on']
        remembered_user_count = len(
            [user for user in six.iteritems(channelstream.USERS)])
        unique_user_count = len(
            [user for user in six.itervalues(channelstream.USERS)
             if user.connections])
        total_connections = sum([len(user.connections)
             for user in six.itervalues(channelstream.USERS)])
        total_sys_connections = len(channelstream.CONNECTIONS.values())
        return {
            "remembered_user_count": remembered_user_count,
            "unique_user_count": unique_user_count,
            "total_connections": total_connections,
            "total_sys_connections": total_sys_connections,
            "total_channels": len(channelstream.CHANNELS.keys()),
            "total_messages": channelstream.stats['total_messages'],
            "total_unique_messages": channelstream.stats[
                'total_unique_messages'],
            "channels": channelstream.CHANNELS,
            "users": channelstream.USERS, "uptime": uptime
        }

    @view_config(route_name='action', match_param='action=info',
                 renderer='json', permission='access')
    def info(self):
        if not self.request.body:
            req_channels = channelstream.CHANNELS.keys()
            info_config = {
                'include_history': True,
                'include_users': True,
                'exclude_channels': [],
                'include_connections': True
            }
        else:
            json_body = self.request.json_body
            # get info config for channel information
            info_config = json_body.get('info') or {}
            req_channels = info_config.get('channels', None)
            info_config['include_connections'] = info_config.get(
                'include_connections', True)
        channels_info = self.get_common_info(req_channels, info_config)
        return channels_info
