import logging
from datetime import datetime

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import forget
from pyramid.response import Response

import gevent
from channelstream import stats, lock
from channelstream.user import User, users
from channelstream.connection import Connection, connections
from channelstream.channel import Channel, channels
from channelstream.ext_json import json
from gevent.queue import Queue, Empty

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
    message = {'user': msg.get('user'),
               'message': msg['message'],
               'type': 'message',
               'timestamp': timestmp}
    pm_users = msg.get('pm_users', [])
    total_sent = 0
    stats['total_unique_messages'] += 1
    if msg.get('channel'):
        channel_inst = channels.get(msg['channel'])
        if channel_inst:
            total_sent += channel_inst.add_message(message,
                                                   pm_users=pm_users)
    elif pm_users:
        # if pm then iterate over all users and notify about new message hiyoo!!
        for username in pm_users:
            user_inst = users.get(username)
            if user_inst:
                total_sent += user_inst.add_message(message)
    stats['total_messages'] += total_sent


class ServerViews(object):
    def __init__(self, request):
        self.request = request

    @view_config(route_name='action', match_param='action=connect',
                 renderer='json', permission='access')
    def connect(self):
        """return the id of connected users - will be secured with password string
        for webapp to internally call the server - we combine conn string with user id,
        and we tell which channels the user is allowed to subscribe to"""
        username = self.request.json_body.get('username')
        def_status = self.request.registry.settings['status_codes']['online']
        user_status = int(self.request.json_body.get('status', def_status))
        channel_configs = self.request.json_body.get('channel_configs', {})
        conn_id = self.request.json_body.get('conn_id')
        subscribe_to_channels = self.request.json_body.get('channels')
        if username is None:
            self.request.response.status = 400
            return {'error': "No username specified"}
        if not subscribe_to_channels:
            self.request.response.status = 400
            return {'error': "No channels specified"}

        # everything is ok so lets add new connection to channel and connection list
        with lock:
            if username not in users:
                user = User(username, def_status)
                users[username] = user
            else:
                user = users[username]
            connection = Connection(username, conn_id)
            if connection.id not in connections:
                connections[connection.id] = connection
            user.add_connection(connection)
            for channel_name in subscribe_to_channels:
                # user gets assigned to a channel
                if channel_name not in channels:
                    channel = Channel(channel_name,
                                      channel_configs=channel_configs)
                    channels[channel_name] = channel
                channels[channel_name].add_connection(connection)
            log.info('connecting %s with uuid %s' % (username, connection.id))
        return {'conn_id': connection.id, 'status': user.status}

    @view_config(route_name='action', match_param='action=subscribe',
                 renderer='json', permission='access')
    def subscribe(self, *args):
        """ call this to subscribe specific connection to new channels """
        conn_id = self.request.json_body.get('conn_id',
                                             self.request.GET.get('conn_id'))
        connection = connections.get(conn_id)
        subscribe_to_channels = self.request.json_body.get('channels')
        channel_configs = self.request.json_body.get('channel_configs', {})
        if not connection:
            self.request.response.status = 403
            return {'error': "Unknown connection"}
        if not subscribe_to_channels:
            self.request.response.status = 400
            return {'error': "No channels specified"}
        # everything is ok so lets add new connection to channel and connection list
        # lets lock it just in case
        # find the right user
        user = users.get(connection.username)
        subscribed_channels = []
        with lock:
            if user:
                for channel_name in subscribe_to_channels:
                    if channel_name not in channels:
                        channel = Channel(channel_name,
                                          channel_configs=channel_configs)
                        channels[channel_name] = channel
                    channels[channel_name].add_connection(connection)
            for channel in channels.itervalues():
                if user.username in channel.connections:
                    subscribed_channels.append(channel.name)
        return subscribed_channels

    @view_config(route_name='action', match_param='action=listen',
                 request_method="OPTIONS", renderer='string')
    def handle_CORS(self):
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
        # self.request.response.headers.add('Access-Control-Allow-Credentials', 'true')
        return ''

    @view_config(route_name='action', match_param='action=listen',
                 renderer='string')
    def listen(self):
        config = self.request.registry.settings
        self.conn_id = self.request.params.get('conn_id')
        connection = connections.get(self.conn_id)
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
            except Empty as e:
                pass
            # get more messages if enqueued takes up total 0.25s
            while True:
                try:
                    messages.extend(connection.queue.get(timeout=0.25))
                except Empty as e:
                    break
            cb = self.request.params.get('callback')
            if cb:
                yield cb + '(' + json.dumps(messages) + ')'
            else:
                yield json.dumps(messages)

        return Response(app_iter=yield_response(), request=self.request,
                        content_type='application/json')

    @view_config(route_name='action', match_param='action=user_status',
                 renderer='json', permission='access')
    def user_status(self):
        """ set the status of specific user """
        username = self.request.json_body.get('user')
        def_status = self.request.registry.settings['status_codes'][
            'online']
        user_status = int(self.request.json_body.get('status', def_status))
        if not username:
            self.request.response.status = 400
            return {'error': "No username specified"}

        user_inst = users.get(username)
        if user_inst:
            user_inst.status = user_status
            # mark active
            user_inst.last_active = datetime.utcnow()
        return {}

    @view_config(route_name='action', match_param='action=message',
                 renderer='json', permission='access')
    def message(self):
        msg_list = self.request.json_body
        for msg in msg_list:
            if not msg.get('channel') and not msg.get('pm_users', []):
                continue
            gevent.spawn(pass_message, msg, stats)

    @view_config(route_name='action', match_param='action=disconnect',
                 renderer='json', permission='access')
    def disconnect(self):
        conn_id = self.request.json_body.get('conn_id',
                                             self.request.GET.get('conn_id'))
        conn = connections.get(conn_id)
        if conn is not None:
            conn.mark_for_gc()

    @view_config(route_name='action', match_param='action=channel_config',
                 renderer='json', permission='access')
    def channel_config(self):
        """ call this to reconfigure channel """
        channel_data = self.request.json_body
        if not channel_data:
            self.request.response.status = 400
            return {'error': "No channels specified"}

        json_data = []
        with lock:
            for channel_name, config in channel_data:
                if not channel:
                    channel = Channel(channel_name, )
                    channels[channel_name] = channel
                channel = channels[channel_name]
                for k, v in config.iteritems():
                    setattr(channel, k, v)
                json_data.append({'name': channel.name,
                                  'long_name': channel.long_name,
                                  'notify_presence': channel.notify_presence,
                                  'salvageable': channel.salvageable,
                                  'store_history': channel.store_history,
                                  'history_size': channel.history_size})
        return json_data

    @view_config(
        context='channelstream.wsgi_views.wsgi_security:RequestBasicChannenge')
    def admin_challenge(self):
        response = HTTPUnauthorized()
        response.headers.update(forget(self.request))
        return response

    @view_config(route_name='admin',
                 renderer='templates/admin.jinja2', permission='access')
    def admin(self):
        uptime = datetime.utcnow() - stats['started_on']
        remembered_user_count = len(
            [user for user in users.iteritems()])
        unique_user_count = len(
            [user for user in users.itervalues() if
             user.connections])
        total_connections = sum(
            [len(user.connections) for user in users.itervalues()])
        return {
            "remembered_user_count": remembered_user_count,
            "unique_user_count": unique_user_count,
            "total_connections": total_connections,
            "total_messages": stats['total_messages'],
            "total_unique_messages": stats['total_unique_messages'],
            "channels": channels,
            "users": users, "uptime": uptime
        }

    @view_config(route_name='action', match_param='action=info',
                 renderer='json', permission='access')
    def info(self):
        start_time = datetime.now()

        json_data = {"channels": {}, "unique_users": len(users)}

        # select everything for empty list
        if not self.request.body or not self.request.json_body.get('channels'):
            req_channels = channels.keys()
        else:
            req_channels = self.request.json_body['channels']
        # return requested channel info
        for channel_inst in [chan for chan in channels.values() if
                             chan.name in req_channels]:
            json_data["channels"][channel_inst.name] = {}
            json_data["channels"][channel_inst.name]['total_users'] = len(
                channel_inst.connections)
            json_data["channels"][channel_inst.name]['total_connections'] = sum(
                [len(conns) for conns in channel_inst.connections.values()])
            json_data["channels"][channel_inst.name]['users'] = []
            for username in channel_inst.connections.keys():
                user_inst = users.get(username)
                udata = {'user': user_inst.username,
                         'status': user_inst.status,
                         "connections": [conn.id for conn in
                                         channel_inst.connections[username]]}
                json_data["channels"][channel_inst.name]['users'].append(udata)
            json_data["channels"][channel_inst.name][
                'last_active'] = channel_inst.last_active
        log.info('info time: %s' % (datetime.now() - start_time))
        return json_data
