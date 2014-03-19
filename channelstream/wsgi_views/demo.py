import json
import random
import uuid

import requests
from pyramid.view import view_config


possible_channels = set(['pub_chan', 'pub_chan2', 'notify'])


class DemoViews(object):
    def __init__(self, request):
        self.request = request
        self.request.response.headers.add('Cache-Control', 'no-cache, no-store')
        self.server_port = self.request.registry.server_config['port']
        self.secret_headers = {'x-channelstream-secret': 'secret',
                               'Content-Type': 'application/json'}

    @view_config(route_name='section_action', renderer='string',
                 request_method="OPTIONS")
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
        return {}

    @view_config(route_name='demo', renderer='templates/demo.jinja2')
    def demo(self):
        return {
            'webapp_url': 'http://127.0.0.1:%s/demo' % self.server_port,
            'server_url': 'ws://127.0.0.1:%s' % self.server_port}


    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=connect'],
                 renderer='json', request_method="POST")
    def connect(self):
        """handle authorization of users trying to connect"""
        channels = self.request.json_body['channels']
        possible_channels.intersection(channels)
        random_name = 'anon_%s' % random.randint(1, 999999)
        payload = {"user": random_name,
                   "conn_id": str(uuid.uuid4()),
                   "channels": channels
        }
        url = 'http://127.0.0.1:%s/connect' % self.server_port
        response = requests.post(url, data=json.dumps(payload),
                                 headers=self.secret_headers).json()
        payload['status'] = response['status']
        return payload

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=subscribe'],
                 renderer='json', request_method="POST")
    def subscribe(self):
        """"can be used to subscribe specific connection to other channels"""
        self.request_data = self.request.json_body
        channels = self.request_data['channels']
        possible_channels.intersection(channels)
        payload = {"conn_id": self.request_data.get('conn_id', ''),
                   "channels": self.request_data.get('channels', [])
        }
        url = 'http://127.0.0.1:%s/subscribe' % self.server_port
        response = requests.post(url, data=json.dumps(payload),
                                 headers=self.secret_headers).json()
        return response

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=message'],
                 renderer='json', request_method="POST")
    def message(self):
        """send message to channel/users"""
        self.request_data = self.request.json_body
        payload = {
            'type': 'message',
            "user": self.request_data.get('user', 'system'),
            "channel": self.request_data.get('channel', 'unknown_channel'),
            'message': self.request_data.get('message')
        }
        url = 'http://127.0.0.1:%s/message' % self.server_port
        response = requests.post(url, data=json.dumps([payload]),
                                 headers=self.secret_headers).json()
        return response

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=channel_config'],
                 renderer='json', request_method="POST")
    def channel_config(self):
        """configure channel defaults"""
        payload = [('pub_chan', {
            "presence": True,
            "store_history": True,
            "history_size": 20
        }),
                   ('pub_chan2', {
                       "presence": True,
                       "salvagable": True,
                       "store_history": True,
                       "history_size": 30
                   })
        ]
        url = 'http://127.0.0.1:%s/channel_config' % self.server_port
        response = requests.post(url, data=json.dumps(payload),
                                 headers=self.secret_headers).json()
        return response