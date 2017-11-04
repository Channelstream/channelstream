class ChatUserList extends Polymer.Element {

    static get is() {
        return 'chat-user-list';
    }

    static get properties() {
        return {
            users: Array,
            usersStates: Object
        };
    }

    _computedEmail(op, username) {
        return this.usersStates[username].state.email;
    }
    _computedColor(op, username){
        return this.usersStates[username].state.color || 'black';
    }
}

customElements.define(ChatUserList.is, ChatUserList);
