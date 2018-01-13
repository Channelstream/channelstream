class ChatChannelPicker extends Polymer.mixinBehaviors([Polymer.IronResizableBehavior], Polymer.Element) {
    static get is() {
        return 'chat-channel-picker';
    }

    static get properties() {
        return {
            possibleChannels: Array,
            subscribedChannels: Array
        };
    }

    subscribeToChannel(event) {
        this.dispatchEvent(new CustomEvent('channelpicker-subscribe', {
            detail: {channel: event.currentTarget.get('channel')},
            bubbles: true,
            composed: true
        }));
    }

    _computedConnectIcon(subscribedChannels, channel) {
        if (subscribedChannels.indexOf(channel) !== -1) {
            return 'icons:check-box';
        }
        return 'icons:check-box-outline-blank';
    }

    _computedConnectLabel(subscribedChannels, channel) {
        if (subscribedChannels.indexOf(channel) !== -1) {
            return 'Connected to "' + channel + '"';
        }
        return 'Connect to "' + channel + '"';
    }
}

customElements.define(ChatChannelPicker.is, ChatChannelPicker);
