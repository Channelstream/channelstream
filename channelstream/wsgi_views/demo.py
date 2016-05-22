import json
import random
import uuid
import requests
import six
from pyramid.view import view_config
from itsdangerous import TimestampSigner

POSSIBLE_CHANNELS = set(['pub_chan', 'pub_chan2', 'notify'])


def make_request(request, payload, endpoint):
    server_port = request.registry.settings['port']
    signer = TimestampSigner(request.registry.settings['secret'])
    sig_for_server = signer.sign(endpoint)
    if not six.PY2:
        sig_for_server = sig_for_server.decode('utf8')
    secret_headers = {'x-channelstream-secret': sig_for_server,
                      'x-channelstream-endpoint': endpoint,
                      'Content-Type': 'application/json'}
    url = 'http://127.0.0.1:%s%s' % (server_port, endpoint)
    response = requests.post(url, data=json.dumps(payload),
                             headers=secret_headers)
    return response.json()


def enable_demo(context, request):
    if request.registry.settings['demo']:
        return True
    return False


CHANNEL_CONFIGS = {"pub_chan": {"notify_presence": True},
                   "notify": {"notify_presence": True}}


class DemoViews(object):
    def __init__(self, request):
        self.request = request
        self.request.response.headers.add('Cache-Control',
                                          'no-cache, no-store')

    @view_config(route_name='section_action', renderer='string',
                 request_method="OPTIONS", custom_predicates=[enable_demo])
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
        # self.request.response.headers.add('Access-Control-Allow-Credentials',
        # 'true')
        return {}

    @view_config(route_name='demo', renderer='templates/demo.jinja2',
                 custom_predicates=[enable_demo])
    def demo(self):
        random_name = 'anon_%s' % random.randint(1, 999999)
        return {'username': random_name}

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=connect'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def connect(self):
        """handle authorization of users trying to connect"""
        channels = self.request.json_body['channels']
        POSSIBLE_CHANNELS.intersection(channels)
        random_name = 'anon_%s' % random.randint(1, 999999)
        username = self.request.json_body.get('username', random_name)

        payload = {"username": username,
                   "conn_id": str(uuid.uuid4()),
                   "channels": channels,
                   "channel_configs": CHANNEL_CONFIGS}
        make_request(self.request, payload, '/connect')
        return payload

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=subscribe'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def subscribe(self):
        """"can be used to subscribe specific connection to other channels"""
        request_data = self.request.json_body
        channels = request_data['channels']
        POSSIBLE_CHANNELS.intersection(channels)
        payload = {"conn_id": request_data.get('conn_id', ''),
                   "channels": request_data.get('channels', []),
                   "channel_configs": CHANNEL_CONFIGS
                   }
        result = make_request(self.request, payload, '/subscribe')
        return result['channels']

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=unsubscribe'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def unsubscribe(self):
        """"can be used to subscribe specific connection to other channels"""
        request_data = self.request.json_body
        payload = {"conn_id": request_data.get('conn_id', ''),
                   "channels": request_data.get('channels', [])
                   }
        result = make_request(self.request, payload, '/unsubscribe')
        return result['channels']

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=message'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def message(self):
        """send message to channel/users"""
        request_data = self.request.json_body
        payload = {
            'type': 'message',
            "user": request_data.get('user', 'system'),
            "channel": request_data.get('channel', 'unknown_channel'),
            'message': request_data.get('message')
        }
        result = make_request(self.request, [payload], '/message')
        return result

    @view_config(route_name='section_action',
                 match_param=['section=demo', 'action=channel_config'],
                 renderer='json', request_method="POST",
                 custom_predicates=[enable_demo])
    def channel_config(self):
        """configure channel defaults"""

        payload = [
            ('pub_chan', {
                "notify_presence": True,
                "store_history": True,
                "history_size": 20
            }),
            ('pub_chan2', {
                "notify_presence": True,
                "salvageable": True,
                "store_history": True,
                "history_size": 30
            })
        ]
        url = 'http://127.0.0.1:%s/channel_config' % self.server_port
        response = requests.post(url, data=json.dumps(payload),
                                 headers=self.secret_headers).json()
        return response
