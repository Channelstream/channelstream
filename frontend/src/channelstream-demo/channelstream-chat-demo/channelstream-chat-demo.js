import {ReduxMixin} from '../redux/store';
import {actions as currentActions} from '../../channelstream-admin/redux/current_actions';

class ChannelStreamChatDemo extends ReduxMixin(Polymer.Element) {

    static get is() {
        return 'channelstream-chat-demo';
    }

    static get properties() {
        return {
            isReady: Boolean,
            user: {
                type: Object,
                value: function() {
                    return {
                        username: 'Anonymous_' + String(Math.floor(Math.random() * 10000)),
                        email: ''
                    };
                }
            },
            channels: {
                type: Array,
                value: function() {
                    return ['pub_chan'];
                }
            },
            possibleChannels: {
                type: Array,
                value: function() {
                    return ['notify', 'pub_chan', 'second_channel']
                }
            },
            userState: {
                type: Object,
                value: function() {
                    return {};
                },
                notify: true
            },
            usersStates: {
                type: Object,
                value: function() {
                    return {};
                },
                notify: true
            },
            channelsStates: {
                type: Object,
                value: function() {
                    return {};
                },
                notify: true
            },
            page: {
                type: String,
                value: 'chat',
                notify: true
            }
        };
    }

    static get observers() {
        return [
            // Observer method name, followed by a list of dependencies, in parenthesis
            'routePageChanged(routeData.page)',
            'pageChanged(page)',
            'handleUserChange(user.*)'
        ];
    }

    /** mediator pattern pushes events from connection to chat view */
    receivedMessage(event) {
        var chatView = this.shadowRoot.querySelector('chat-view');
        for (var i = 0; i < event.detail.length; i++) {
            var message = event.detail[i];
            if (['message', 'presence'].indexOf(message.type) !== -1) {
                chatView.addMessage(message);
            }
            // update users on presence message
            if (message.type === 'presence') {
                // push channel and user states for newly joined user
                if (message.message.action === 'joined') {
                    this.push(['channelsStates',
                        message.channel, 'users'], message.user);
                    this.set(
                        ['usersStates', message.user],
                        {state: message.state, user: message.user})
                }
                else {
                    var ix = this.channelsStates[message.channel].users.indexOf(message.user);
                    this.splice(['channelsStates', message.channel, 'users'], ix, 1);
                }
            }
            if (message.type === 'user_state_change'){
                this.set(['usersStates', message.user, 'state'], message.message.state)
            }
        }
    }
    /** sends the message via channelstream conn manageer */
    sendMessage(event) {
        this.getConnection().message(event.detail);
    }
    changeStatus(event){
        var stateUpdates = event.detail;
        this.getConnection().updateUserState({user_state:stateUpdates});
    }

    /** kicks off the connection */
    ready() {
        super.ready();
        this.isReady = true;
        var channelstreamConnection = this.shadowRoot.querySelector('channelstream-connection');
        channelstreamConnection.connectUrl = AppConf.connectUrl;
        channelstreamConnection.disconnectUrl = AppConf.disconnectUrl;
        channelstreamConnection.subscribeUrl = AppConf.subscribeUrl;
        channelstreamConnection.unsubscribeUrl = AppConf.unsubscribeUrl;
        channelstreamConnection.messageUrl = AppConf.messageUrl;
        channelstreamConnection.longPollUrl = AppConf.longPollUrl;
        channelstreamConnection.websocketUrl = AppConf.websocketUrl;
        channelstreamConnection.userStateUrl = AppConf.userStateUrl;

        // add a mutator for demo purposes - modify the request
        // to inject some state vars to connection json
        channelstreamConnection.addMutator('connect', function (request) {
            request.body.state = {email: this.user.email, status: 'ready'};
        }.bind(this));
        channelstreamConnection.connect()
    }
    /** creates new connection on name change */
    handleUserChange() {
        if (!this.isReady) {
            return
        }
        var connection = this.shadowRoot.querySelector('channelstream-connection');
        connection.disconnect();
        connection.connect();
    }
    /** subscribes/unsubscribes users from channels in channelstream */
    handleChannelsChange() {
        if (!this.isReady) {
            return
        }
        var connection = this.shadowRoot.querySelector('channelstream-connection');
        var shouldUnsubscribe = connection.calculateUnsubscribe();
        if (shouldUnsubscribe.length > 0) {
            connection.unsubscribe(shouldUnsubscribe);
        }
        else {
            connection.subscribe();
        }
    }
    getConnection() {
        return this.$['channelstream-connection'];
    }

    handleConnected(event) {
        var data = event.detail;
        var chatView = this.shadowRoot.querySelector('chat-view');
        this.set('userState', data.state);
        this.set('channelsStates', data.channels_info.channels);
        this.set('channels', data.channels);
        this.updateUserStates(data.channels_info);
        for (var i = 0; i < data.channels.length; i++) {
            var key = data.channels[i];
            chatView.loadHistory(data.channels_info.channels[key].history, key);
        }
    }

    subscribeToChannel(event) {
        var connection = this.getConnection();
        var channel = event.detail.channel;
        var index = this.get('channels').indexOf(channel);
        if (index !== -1) {
            var toUnsubscribe = connection.calculateUnsubscribe([channel]);
            connection.unsubscribe(toUnsubscribe);
        }
        else {
            var toSubscribe = connection.calculateSubscribe([channel]);
            connection.subscribe(toSubscribe);
        }
    }

    handleSubscribed(event) {
        console.log('handleSubscribed');
        var chatView = this.shadowRoot.querySelector('chat-view');
        var channelInfo = event.detail.channels_info;
        var channelKeys = event.detail.subscribed_to;
        this.set('channels', event.detail.channels);
        this.updateUserStates(channelInfo);
        for (var i = 0; i < channelKeys.length; i++) {
            var key = channelKeys[i];
            this.set(['channelsStates', key], channelInfo.channels[key]);
            chatView.loadHistory(channelInfo.channels[key].history, key);
        }
    }

    handleUnsubscribed(event) {
        var channelKeys = event.detail.unsubscribed_from;
        for (var i = 0; i < channelKeys.length; i++) {
            var key = channelKeys[i];
            this.set(['channelsStates', key], null);
        }
        this.set('channels', event.detail.channels);
    }

    /** updates channel states when we get them returned from connection elem */
    updateUserStates(channels_info) {
        var channel_data = channels_info.channels;
        var user_data = channels_info.users;
        var channels = Object.keys(channel_data);
        for (var i = 0; i < channels.length; i++) {
            var channel = channel_data[channels[i]];
            this.set(['channelsStates', channel.name], channel);
            for (var j = 0; j < channel.users.length; j++) {
                this.set(['usersStates', user_data[j].user], user_data[j]);
            }
        }
    }

    routePageChanged(page) {
        this.page = page || 'chat';
    }

    pageChanged(page) {
        this.set('routeData.page', this.page);
    }
}

customElements.define(ChannelStreamChatDemo.is, ChannelStreamChatDemo);
