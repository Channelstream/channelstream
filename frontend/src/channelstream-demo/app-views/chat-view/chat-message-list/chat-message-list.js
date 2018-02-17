import {ReduxMixin} from '../../../redux/store';

class ChatMessageList extends ReduxMixin(Polymer.mixinBehaviors([Polymer.IronResizableBehavior], Polymer.Element)) {
    static get is() {
        return 'chat-message-list';
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

    static get observers() {
        return [
            // Observer method name, followed by a list of dependencies, in parenthesis
            '_messagesChanged(messages.allIds.splices)'
        ]
    }

    connectedCallback() {
        super.connectedCallback();
        this.notifyResize();
    }

    messageData(messageId) {
        return this.messages.messages[messageId];
    }

    visibleMessages(selectedChannel) {
        return this.messages.channelMessages[this.selectedChannel] || [];
    }

    _messagesChanged() {
        if (this.messages) {
            this.$$('iron-list').scrollToIndex(this.$$('iron-list').items.length - 1);
        }
    }
}

customElements.define(ChatMessageList.is, ChatMessageList);
