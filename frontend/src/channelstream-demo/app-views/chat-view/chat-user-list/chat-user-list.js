import {ReduxMixin} from '../../../redux/store';

class ChatUserList extends ReduxMixin(Polymer.Element) {

    static get is() {
        return 'chat-user-list';
    }

    static get properties() {
        return {
            selectedChannel: {
                type: String
            },
            channelsUsers: {
                type: Object,
                statePath: 'chatView.channels.users'
            },
            users: {
                type: Object,
                statePath: 'chatView.users'
            },
        };
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
