import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../../redux/store.js';

import '@polymer/iron-image/iron-image.js';
import '@polymer/iron-list/iron-list.js';
import '../../../chat-avatar/chat-avatar.js';


class ChatUserList extends connect(store)(PolymerElement) {

    static get template(){
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

        <template is="dom-repeat" items="[[_visibleUsers(selectedChannel, channelsUsers)]]">
            <div class="user" tabindex$="[[tabIndex]]">
                <chat-avatar username="[[item]]" email="[[_computedEmail(usersStates, item)]]"></chat-avatar>
                <span style$="color:{{_computedColor(users, item)}}">[[item]]</span>
            </div>
        </template>
        `
    }

    static get is() {
        return 'chat-user-list';
    }

    static get properties() {
        return {
            selectedChannel: {
                type: String
            },
            channelsUsers: {
                type: Object
            },
            users: {
                type: Object
            },
        };
    }

    _stateChanged(state) {
        this.users = state.chatView.users;
        this.channelsUsers = state.chatView.channels.users;
    }

    _visibleUsers(selectedChannel) {
        return this.channelsUsers[selectedChannel];
    }

    _computedEmail(op, username) {
        return this.users.states[username].email;
    }

    _computedColor(op, username) {
        return this.users.states[username].color || 'black';
    }
}

customElements.define(ChatUserList.is, ChatUserList);
