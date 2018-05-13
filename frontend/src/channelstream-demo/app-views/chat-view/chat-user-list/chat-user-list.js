import {LitElement, html} from '@polymer/lit-element';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../../redux/store.js';

import '@polymer/iron-image/iron-image.js';
import '@polymer/iron-list/iron-list.js';
import '../../../chat-avatar/chat-avatar.js';


class ChatUserList extends connect(store)(LitElement) {

    _render({users, channelsUsers, selectedChannel}) {

        let visibleUsers = [];
        if (channelsUsers.hasOwnProperty(selectedChannel)) {
            visibleUsers = channelsUsers[selectedChannel];
        }
        return html`
        <style>
            chat-avatar {
                float: left;
                margin-right: 10px;
                width: 20px;
                height: 20px;
                --chat-avatar-mixin: {
                    width: 20px;
                    height: 20px;
                }
            }

            .user {
                clear: both;
                margin-bottom: 15px;
            }
        </style>

        ${visibleUsers.map((username) => html`
        <div class="user"> 
            <chat-avatar username=${username} email=${users.states[username].email}></chat-avatar>
            <span style$="color:${users.states[username].color || 'black'}">${username}</span>
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

    _stateChanged(state) {
        this.users = state.chatView.users;
        this.channelsUsers = state.chatView.channels.users;
    }
}

customElements.define(ChatUserList.is, ChatUserList);
