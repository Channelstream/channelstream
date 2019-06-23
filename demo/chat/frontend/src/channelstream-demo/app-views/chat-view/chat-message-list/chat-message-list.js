import {LitElement, html} from 'lit-element';
import '../chat-message/chat-message.js';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../../redux/store.js';


class ChatMessageList extends connect(store)(LitElement) {
    static get is() {
        return 'chat-message-list';
    }

    render(){
        return html`
        <style>
            .message-list {
                width: 100%;
                overflow-y: auto;
            }
        </style>

        <div class="message-list">
        ${(this.messages.channelMessages[this.selectedChannel] || []).map((message, index) => html`
        <chat-message .message=${this.messages.messages[message]} .user=${this.user}></chat-message>
        `)}
        </div>
        `
    }

    static get properties() {
        return {
            messages: Array,
            selectedChannel: String,
            user: Object
        };
    }

    update(){
        super.update();
        setTimeout(() => {
            let listElem = this.shadowRoot.querySelector('.message-list');
            this.scrollTop = this.scrollHeight;
        }, 0)
    }

    stateChanged(state) {
        this.messages = state.chatView.messages;
        this.selectedChannel = state.chatView.ui.selectedChannel;
        this.user = state.user;
    }
}

customElements.define(ChatMessageList.is, ChatMessageList);
