class ChatMessage extends Polymer.Element {

    static get is() {
        return 'chat-message';
    }

    static get properties() {
        return {
            user: String,
            timestamp: Object,
            message: Object,
            channel: String,
            type: String
        };
    }

    _shortTime() {
        return this.timestamp.split('.')[0];
    }
}

customElements.define(ChatMessage.is, ChatMessage);

