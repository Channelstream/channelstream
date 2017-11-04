class ChatChannelPicker extends Polymer.mixinBehaviors([Polymer.IronResizableBehavior], Polymer.Element) {
    static get is() {
        return 'chat-channel-picker';
    }

    static get properties() {
        return {
            channels: Array,
            possibleChannels: Array,
            connectedChannels: {
                type: String,
                computed: '_generateConnectedChannels(channels.*, possibleChannels)'
            }
        };
    }

    static get observers() {
        return [
            // Observer method name, followed by a list of dependencies, in parenthesis
            '_messagesChanged(messages.splices)'
        ];
    }

    subscribeToChannel(event) {
        this.fire('iron-signal', {
            name: 'channelpicker-subscribe',
            data: {channel: event.currentTarget.get('channel')}
        });
    }

    /** pregenerate list of channel states for easier looping */
    _generateConnectedChannels() {
        var channels = [];
        for (var i = 0; i < this.possibleChannels.length; i++) {
            var channel = this.possibleChannels[i];
            channels.push(
                {
                    channel: channel,
                    connected: this.channels.indexOf(channel) !== -1
                }
            );
        }
        return channels;
    }

    _computedConnectIcon(enabled) {
        if (enabled) {
            return 'icons:check-box';
        }
        return 'icons:check-box-outline-blank';
    }

    _computedConnectLabel(enabled, channel) {
        if (enabled) {
            return 'Connected to "' + channel + '"';
        }
        return 'Connect to "' + channel + '"';
    }
}

customElements.define(ChatChannelPicker.is, ChatChannelPicker);
