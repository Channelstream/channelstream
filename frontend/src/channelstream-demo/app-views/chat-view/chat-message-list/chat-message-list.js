import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import '@polymer/iron-list/iron-list.js';
import '../chat-message/chat-message.js';
import {mixinBehaviors} from '@polymer/polymer/lib/legacy/class.js';
import {IronResizableBehavior} from '@polymer/iron-resizable-behavior/iron-resizable-behavior.js';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../../redux/store.js';


class ChatMessageList extends connect(store)(PolymerElement) {
    static get is() {
        return 'chat-message-list';
    }

    static get template(){
        return html`
        <style>
            iron-list {
                height: 500px;
                width: 100%;
            }
        </style>
        <iron-list items="[[visibleMessages(selectedChannel, messages.allIds)]]" as="message" class="chat-list">
            <template>
                <chat-message message="[[messageData(message)]]"></chat-message>
            </template>
        </iron-list>
        `
    }

    static get properties() {
        return {
            messages: {
                type: Array,
                statePath: 'chatView.messages'
            },
            selectedChannel: {
                type: String,
                statePath: 'chatView.ui.selectedChannel'
            }
        };
    }

    _stateChanged(state) {
        this.messages = state.chatView.messages;
        this.selectedChannel = state.chatView.ui.selectedChannel;
    }

    static get observers() {
        return [
            // Observer method name, followed by a list of dependencies, in parenthesis
            '_messagesChanged(messages.allIds.splices)'
        ]
    }

    connectedCallback() {
        super.connectedCallback();
    }

    messageData(messageId) {
        return this.messages.messages[messageId];
    }

    visibleMessages(selectedChannel) {
        return this.messages.channelMessages[this.selectedChannel] || [];
    }

    _messagesChanged() {
        if (this.messages) {
            let listElem = this.shadowRoot.querySelector('iron-list');
            listElem.scrollToIndex(listElem.items.length - 1);
        }
    }
}

customElements.define(ChatMessageList.is, ChatMessageList);
