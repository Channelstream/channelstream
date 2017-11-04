import gravatar from './gravatarjs.js';

class ChatAvatar extends Polymer.Element {

    static get is() {
        return 'chat-avatar';
    }

    static get properties() {
        return {
            email: String,
            username: String
        };
    }

    _getAvatar() {
        var avatar = this.email || this.username || 'test';
        return gravatar(avatar, {
            size: 50, rating: "pg", backup: "retro", secure: true
        });
    }
}

customElements.define(ChatAvatar.is, ChatAvatar);
