import {LitElement, html} from 'lit-element';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../../redux/store.js';
import '../../../chat-avatar/chat-avatar.js';


class ChatUserList extends connect(store)(LitElement) {

    render() {

        let visibleUsers = [];
        if (this.channelsUsers.hasOwnProperty(this.selectedChannel)) {
            visibleUsers = this.channelsUsers[this.selectedChannel];
        }
        return html`
        <style>
            chat-avatar {
                display: inline-block;
                margin-right: 10px;
                width: 20px;
                height: 20px;
                --chat-avatar-width: 20px;
                --chat-avatar-height: 20px;
                }
            }

            .user {
                clear: both;
                margin-bottom: 15px;
            }
        </style>

        ${visibleUsers.map((username) => html`
        <div class="user">
            <chat-avatar .username=${username} .email=${this.users.states[username].email}></chat-avatar>
            <span style="color:${this.users.states[username].color || 'black'}">${username}</span>
        </div>
        `)}
        `
    }

    static get is() {
        return 'chat-user-list';
    }

    static get properties() {
        return {
            selectedChannel: String,
            channelsUsers: Object,
            users: Object,
        };
    }

    stateChanged(state) {
        this.users = state.chatView.users;
        this.channelsUsers = state.chatView.channels.users;
    }
}

customElements.define(ChatUserList.is, ChatUserList);
