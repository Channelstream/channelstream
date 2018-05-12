import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import '@polymer/iron-image/iron-image.js';
import gravatar from './gravatarjs.js';

class ChatAvatar extends PolymerElement {

    static get template(){
        return html`
        <style>
            iron-image {
                border-radius: 25px;
                border: 3px solid #eeeeee;

                width: 50px;
                height: 50px;
                background-color: #ffffff;
                @apply(--chat-avatar-mixin);
            }
        </style>
        <iron-image sizing="cover" src="[[_getAvatar(username, email)]]" preload fade></iron-image>
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

    _getAvatar() {
        var avatar = this.email || this.username || 'test';
        return gravatar(avatar, {
            size: 50, rating: "pg", backup: "retro", secure: true
        });
    }
}

customElements.define(ChatAvatar.is, ChatAvatar);
