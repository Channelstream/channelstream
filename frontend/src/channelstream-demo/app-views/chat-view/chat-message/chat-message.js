class ChatMessage extends Polymer.Element {

    static get is() {
        return 'chat-message';
    }

    static get properties() {
        return {
            message: Object
        };
    }

    _shortTime() {
        return this.message.timestamp.split('.')[0];
    }
}

customElements.define(ChatMessage.is, ChatMessage);

