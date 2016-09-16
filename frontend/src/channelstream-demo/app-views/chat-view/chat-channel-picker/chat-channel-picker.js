Polymer({
    is: 'chat-channel-picker',
    // this is required so we can pass visible/hidden state to message list and iron-list
    behaviors: [
        Polymer.IronResizableBehavior
    ],
    properties: {
        channels: Array,
        possibleChannels: Array,
        connectedChannels: {
            type: String,
            computed: '_generateConnectedChannels(channels.*, possibleChannels)'
        }
    },
    subscribeToChannel: function (event) {
        var app = document.getElementsByTagName('channelstream-chat-demo')[0];
        var connection = app.getConnection();
        var channel = event.currentTarget.get('channel');
        var index = this.get('channels').indexOf(channel);
        if (index !== -1) {
            var toUnsubscribe = connection.calculateUnsubscribe([channel]);
            connection.unsubscribe(toUnsubscribe);
        }
        else {
            var toSubscribe = connection.calculateSubscribe([channel]);
            connection.subscribe(toSubscribe);
        }
    },
    /** pregenerate list of channel states for easier looping */
    _generateConnectedChannels: function () {
        var channels = [];
        for (var i = 0; i < this.possibleChannels.length; i++) {
            var channel = this.possibleChannels[i];
            channels.push(
                {
                    channel: channel,
                    connected: this.channels.indexOf(channel) !== -1
                }
            )
        }
        return channels;
    },

    _computedConnectIcon: function (enabled) {
        if (enabled) {
            return 'icons:check-box'
        }
        return 'icons:check-box-outline-blank'
    },
    _computedConnectLabel: function (enabled, channel) {
        if (enabled) {
            return 'Connected to "' + channel + '"'
        }
        return 'Connect to "' + channel + '"'
    }
});
