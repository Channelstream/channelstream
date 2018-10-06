import {LitElement, html} from '@polymer/lit-element';
import '@polymer/paper-button/paper-button.js';
import '@polymer/iron-icon/iron-icon.js';


class ChatChannelPicker extends LitElement {
    static get is() {
        return 'chat-channel-picker';
    }

    render() {
        return html`
        ${this.possibleChannels.map((channel) => html`
        <paper-button raised @tap=${(e) => this.subscribeToChannel(e, channel)}>
        <iron-icon .icon="icons:${(this.subscribedChannels.indexOf(channel) !== -1 ? 'check-box' : 'check-box-outline-blank')}">
        </iron-icon>
        ${this.subscribedChannels.indexOf(channel) !== -1 ? 'Connected to ' : 'Connect to'} "${channel}"
        </paper-button>`)}
        `
    }

    constructor(){
        super();
    }

    static get properties() {
        return {
            possibleChannels: Array,
            subscribedChannels: Array
        };
    }

    subscribeToChannel(event, channel) {
        this.dispatchEvent(new CustomEvent('channelpicker-subscribe', {
            detail: {channel: channel},
            bubbles: true,
            composed: true
        }));
    }
}

customElements.define(ChatChannelPicker.is, ChatChannelPicker);
