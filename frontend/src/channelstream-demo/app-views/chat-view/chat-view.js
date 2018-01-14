import {ReduxMixin} from '../../redux/store';
import {actions as currentActions} from "../../../channelstream-admin/redux/current_actions";
import {actions as userActions} from '../../redux/user';
import {actions as channelViewUiActions} from '../../redux/chat_view/ui';

class ChatView extends ReduxMixin(Polymer.mixinBehaviors([Polymer.IronResizableBehavior], Polymer.Element)) {
    static get is() {
        return 'chat-view';
    }

    static get properties() {
        return {
            channels: {
                type: Array,
                statePath: 'chatView.channels'
            },
            possibleChannels: {
                type: Array,
                statePath: 'chatView.possibleChannels'
            },
            selectedChannel: {
                type: String,
                statePath: 'chatView.ui.selectedChannel'
            },
            user: {
                type: Array,
                statePath: 'user'
            },
            users: {
                type: Array,
                statePath: 'chatView.users'
            },
        };
    }

    static get actions() {
        return {
            ...currentActions,
            setUser: userActions.set,
            setUserState: userActions.setState,
            setViewedChannel: channelViewUiActions.setViewedChannel
        };
    }

    attached() {
        this.async(this.notifyResize, 1);
    }

    selectedChannelChanged(event) {
        console.log('selectedChannelChanged', event.detail.value);
        this.dispatch('setViewedChannel', event.detail.value);
    }


    /** Act only on various message types */
    addMessage(message) {
        // create a new key for channel
        if (typeof this.messages[message.channel] === 'undefined') {
            this.messages[message.channel] = [];
        }

        // push message
        if (message.type === 'message') {
            this.push(['messages', message.channel], message);
        }
        else if (message.type === 'presence') {
            var text = 'User ' + message.user + ' ' + message.message.action;
            // set presence text and normalize to format message element expects
            message.message = {
                text: text,
                email: '',
                action: message.message.action
            };
            this.push(['messages', message.channel], message);
        }
    }

    loadHistory(messageList, channel) {
        this.set(['messages', channel], messageList);
    }

    openDialog() {
        this.$.loginDialog.open();
    }

    changeUser(event) {
        event.preventDefault();
        if (this.$['login-form'].validate()) {
            this.dispatch('setUser', {
                username: this.loginUsername,
                email: this.loginEmail
            });
            this.$.loginDialog.close();
        }
    }

    /** stop default form submit because shady dom might fire it twice */
    formPresubmit(event) {
        event.preventDefault();
    }

    /** sends the signal that will pass the message to the
     * channelstream-connection element */
    sendMessage(event) {
        event.preventDefault();
        this.fire('iron-signal', {
            name: 'send-message',
            data: {
                message: {
                    text: this.message,
                    email: this.user.email,
                },
                channel: this.selectedChannel,
                user: this.user.username,
            }
        });
        this.shadowRoot.querySelector('#message-form paper-input').value = '';
    }
}

customElements.define(ChatView.is, ChatView);
