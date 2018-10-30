import {LitElement, html} from '@polymer/lit-element';
import '@polymer/iron-image/iron-image.js';
import gravatar from './gravatarjs.js';

class ChatAvatar extends LitElement {

    render(){
        return html`
        <style>
            iron-image {
                border-radius: 25px;
                border: 3px solid #eeeeee;
                background-color: #ffffff;
                width: var(--chat-avatar-width, 50px);
                height: var(--chat-avatar-height, 50px);
            }
        </style>
        <iron-image sizing="cover" .src=${this._getAvatar(this.username, this.email)} preload fade></iron-image>
        `
    }

    static get is() {
        return 'chat-avatar';
    }

    static get properties() {
        return {
            email: String,
            username: String
        };
    }

    _getAvatar(email, username) {
        let avatar = email || username || 'test';
        return gravatar(avatar, {
            size: 50, rating: "pg", backup: "retro", secure: true
        });
    }
}

customElements.define(ChatAvatar.is, ChatAvatar);
