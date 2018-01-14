class ChatMessage extends Polymer.Element {

    static get is() {
        return 'chat-message';
    }

    static get properties() {
        return {
            message: Object
        };
    }

    constructor(){
        super();
        // this is just for some debug fun
        this.random = Math.random();
    }

    _messageText() {
        let txt = this.message.message.action;
        return this.message.message.text || `User ${txt}`;
    }

    _shortTime() {
        return this.message.timestamp.split('.')[0];
    }
}

customElements.define(ChatMessage.is, ChatMessage);

