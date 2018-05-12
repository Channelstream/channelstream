import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import '@polymer/paper-button/paper-button.js';
import '@polymer/iron-icon/iron-icon.js';


class ChatChannelPicker extends PolymerElement {
    static get is() {
        return 'chat-channel-picker';
    }

    static get template(){
        return html`
        <template is="dom-repeat" items="[[possibleChannels]]">
            <paper-button raised on-tap="subscribeToChannel" channel="[[item]]">
                <iron-icon icon="[[_computedConnectIcon(subscribedChannels, item)]]"></iron-icon>
                [[_computedConnectLabel(subscribedChannels, item)]]
            </paper-button>
        </template>
        `
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
