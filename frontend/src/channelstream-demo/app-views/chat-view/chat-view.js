import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../redux/store.js';

import '@polymer/iron-a11y-keys/iron-a11y-keys.js';
import '@polymer/iron-form/iron-form.js';
import '@polymer/iron-resizable-behavior/iron-resizable-behavior.js';
import '@polymer/paper-dialog/paper-dialog.js';
import '@polymer/paper-button/paper-button.js';
import '@polymer/paper-input/paper-input.js';
import '@polymer/paper-icon-button/paper-icon-button.js';
import '@polymer/paper-tabs/paper-tabs.js';
import '@polymer/iron-flex-layout/iron-flex-layout-classes.js';
import {mixinBehaviors} from '@polymer/polymer/lib/legacy/class.js';
import {IronResizableBehavior} from '@polymer/iron-resizable-behavior/iron-resizable-behavior.js';

import './chat-message-list/chat-message-list.js';
import './chat-channel-picker/chat-channel-picker.js';
import './chat-user-list/chat-user-list.js';
import './chat-status-selector/chat-status-selector.js';

import {actions as currentActions} from "../../../channelstream-admin/redux/current_actions";
import {actions as userActions} from '../../redux/user';
import {actions as channelViewUiActions} from '../../redux/chat_view/ui';

class ChatView extends connect(store)(PolymerElement) {


    static get template() {
        return html`
            <style include="iron-flex iron-flex-alignment">
            :host > *{
                --paper-tabs-selection-bar-color: #4285f4;
                --paper-tab-ink: #4285f4;
            }
            .right-column {
                width: 250px;
                margin-left: 30px;
            }

            .left-column {
                @apply(--layout-flex);
            }

            #message-input {
                display: inline-block;
                min-width: 50%;
            }

            paper-tabs {
                display: inline-flex;
            }
        </style>

        <paper-dialog id="loginDialog" with-backdrop>
            <p>Log in to post messages</p>

            <iron-form id="login-form">
            <form method="post" on-iron-form-presubmit="formPresubmit">
                <iron-a11y-keys id="a11y" keys="enter" on-keys-pressed="changeUser"></iron-a11y-keys>
                <paper-input value="{{loginUsername}}" label="User Name" min-length="1" auto-validate required></paper-input>
                <paper-input value="{{loginEmail}}" label="Email" min-length="1" auto-validate required></paper-input>
            </form>
            </iron-form>


            <div class="buttons">
                <paper-button on-tap="changeUser" autofocus>Confirm credentials</paper-button>
            </div>
        </paper-dialog>

        <div class="layout horizontal">
            <div class="left-column">
                <paper-tabs selected="[[selectedChannel]]" attr-for-selected="name"
                            on-selected-changed="selectedChannelChanged">
                    <template is="dom-repeat" items="[[user.subscribedChannels]]">
                        <paper-tab name="[[item]]">Channel: [[item]]</paper-tab>
                    </template>
                </paper-tabs>
                <chat-message-list></chat-message-list>
            </div>
            <div class="right-column">
                <chat-status-selector></chat-status-selector>
                <chat-user-list selected-channel="[[selectedChannel]]"></chat-user-list>
            </div>

        </div>
        <iron-form id="message-form" on-iron-form-presubmit="formPresubmit">
        <form method="post">
            <iron-a11y-keys id="a11y" keys="enter" on-keys-pressed="sendMessage"></iron-a11y-keys>
            <paper-input id="message-input" name="message" label="Your message" value="{{message}}"></paper-input>
            <paper-icon-button icon="icons:send" on-tap="sendMessage"></paper-icon-button>
            <br/>
            <template is="dom-if" if="[[user.anonymous]]">
                <paper-button on-tap="openDialog" raised>
                    <iron-icon icon="social:person-outline"></iron-icon>
                    Change username
                </paper-button>
            </template>
            <chat-channel-picker subscribed-channels="[[user.subscribedChannels]]"
                                 possible-channels="[[possibleChannels]]"></chat-channel-picker>
        </form>
        </iron-form>
        
        `
    }

    static get is() {
        return 'chat-view';
    }

    static get properties() {
        return {
            channels: {
                type: Array
            },
            possibleChannels: {
                type: Array
            },
            selectedChannel: {
                type: String
            },
            user: {
                type: Array
            },
            users: {
                type: Array
            },
        };
    }

    _stateChanged(state) {
        this.user = state.user;
        this.channels = state.chatView.channels;
        this.possibleChannels = state.chatView.ui.possibleChannels;
        this.selectedChannel = state.chatView.ui.selectedChannel;
        this.user = state.user;
        this.users = state.chatView.users;
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
        store.dispatch(channelViewUiActions.setViewedChannel(event.detail.value));
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
            store.dispatch(userActions.set({
                username: this.loginUsername,
                email: this.loginEmail
            }));
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
        this.dispatchEvent(new CustomEvent('send-message',
            {
                detail: {
                    message: {
                        text: this.message,
                        email: this.user.email,
                    },
                    channel: this.selectedChannel,
                    user: this.user.username,
                },
                composed: true, bubbles: true
            }));
        this.shadowRoot.querySelector('#message-form paper-input').value = '';
    }
}

customElements.define(ChatView.is, ChatView);
