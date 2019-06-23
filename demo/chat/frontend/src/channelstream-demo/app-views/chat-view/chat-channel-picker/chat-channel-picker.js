import {LitElement, html} from 'lit-element';
import '@material/mwc-button/mwc-button.js';
import '@material/mwc-icon/mwc-icon.js';


class ChatChannelPicker extends LitElement {
    static get is() {
        return 'chat-channel-picker';
    }

    render() {
        return html`
        ${this.possibleChannels.map((channel) => html`
        <mwc-button outlined @click=${(e) => this.subscribeToChannel(e, channel)}>
        <mwc-icon>${(this.subscribedChannels.indexOf(channel) !== -1 ? 'check_box' : 'check_box_outline_blank')}</mwc-icon>
        ${this.subscribedChannels.indexOf(channel) !== -1 ? 'Connected to ' : 'Connect to'} "${channel}"
        </mwc-button>`)}
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
