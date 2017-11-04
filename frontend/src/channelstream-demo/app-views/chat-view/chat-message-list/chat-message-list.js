class ChatMessageList extends Polymer.mixinBehaviors([Polymer.IronResizableBehavior], Polymer.Element) {
    static get is() {
        return 'chat-message-list';
    }

    static get properties() {
        return {
            messages: Array
        };
    }

    static get observers() {
        return [
            // Observer method name, followed by a list of dependencies, in parenthesis
            '_messagesChanged(messages.splices)'
        ]
    }

    attached() {
        this.notifyResize();
    }

    _messagesChanged() {
        if (this.messages) {
            this.$$('iron-list').scrollToIndex(this.messages.length - 1);
        }
    }
}

customElements.define(ChatMessageList.is, ChatMessageList);
