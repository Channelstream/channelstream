import {LitElement, html} from '@polymer/lit-element';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../redux/store.js';

import '@polymer/iron-a11y-keys/iron-a11y-keys.js';
import '@polymer/iron-form/iron-form.js';
import '@polymer/paper-dialog/paper-dialog.js';
import '@polymer/paper-button/paper-button.js';
import '@polymer/paper-input/paper-input.js';
import '@polymer/paper-icon-button/paper-icon-button.js';
import '@polymer/paper-tabs/paper-tabs.js';
import '@polymer/iron-flex-layout/iron-flex-layout-classes.js';

import './chat-message-list/chat-message-list.js';
import './chat-channel-picker/chat-channel-picker.js';
import './chat-user-list/chat-user-list.js';
import './chat-status-selector/chat-status-selector.js';

import {actions as userActions} from '../../redux/user';
import {actions as channelViewUiActions} from '../../redux/chat_view/ui';

class ChatView extends connect(store)(LitElement) {


    _render({user, possibleChannels, selectedChannel}) {

        let dialogButton = null;
        if (user.anonymous){
            dialogButton = html`
                <paper-button on-tap=${(e) => this.openDialog(e)} raised>
                <iron-icon icon="social:person-outline"></iron-icon>
                Change username
                </paper-button>
            `
        }

        return html`
            <style>
            #column-holder{
            display: flex;
            }
            
            :host > *{
                --paper-tabs-selection-bar-color: #4285f4;
                --paper-tab-ink: #4285f4;
            }
            .right-column {
                width: 250px;
                margin-left: 30px;
            }

            .left-column {
                flex-grow: 1;
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
            <form method="post" on-iron-form-presubmit=${(e) => this.formPresubmit(e)}>
                <iron-a11y-keys id="a11y" keys="enter" on-keys-pressed=${(e) => this.changeUser(e)}></iron-a11y-keys>
                <paper-input label="User Name" name="username" min-length="1" auto-validate required></paper-input>
                <paper-input label="Email" name="email" min-length="1" auto-validate required></paper-input>
            </form>
            </iron-form>


            <div class="buttons">
                <paper-button on-tap=${(e) => this.changeUser(e)} autofocus>Confirm credentials</paper-button>
            </div>
        </paper-dialog>

        <div id="column-holder">
            <div class="left-column">
                <paper-tabs selected=${selectedChannel} attr-for-selected="name"
                            on-selected-changed=${(e) => this.selectedChannelChanged(e)}>
                            
                    ${user.subscribedChannels.map((channel) => html`
                    <paper-tab name=${channel}>Channel: ${channel}</paper-tab>
                    `) }
                </paper-tabs>
                <chat-message-list></chat-message-list>
            </div>
            <div class="right-column">
                <chat-status-selector></chat-status-selector>
                <chat-user-list selectedChannel=${selectedChannel}></chat-user-list>
            </div>

        </div>
        <iron-form id="message-form" on-iron-form-presubmit=${(e) => this.formPresubmit(e)}>
            <form method="post">
                <iron-a11y-keys id="a11y" keys="enter" on-keys-pressed=${(e) => this.sendMessage(e)}></iron-a11y-keys>
                <paper-input id="message-input" name="message" label="Your message"></paper-input>
                <paper-icon-button icon="icons:send" on-tap=${(e) => this.sendMessage(e)}></paper-icon-button>
                <br/>
                ${dialogButton}
                <chat-channel-picker subscribedChannels=${user.subscribedChannels}
                                     possibleChannels=${possibleChannels}></chat-channel-picker>
            </form>        
        </iron-form>
        `
    }

    static get is() {
        return 'chat-view';
    }

    static get properties() {
        return {
            channels: Array,
            // what we can subscribe to
            possibleChannels: Array,
            selectedChannel: String,
            user: Object,
            users: Array,
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

    selectedChannelChanged(event) {
        console.log('selectedChannelChanged', event.detail.value);
        store.dispatch(channelViewUiActions.setViewedChannel(event.detail.value));
    }

    loadHistory(messageList, channel) {
        this.set(['messages', channel], messageList);
    }

    openDialog() {
        this.shadowRoot.querySelector('paper-dialog').open();
    }

    changeUser(event) {
        event.preventDefault();
        let loginForm = this.shadowRoot.querySelector('#login-form');
        let formData = loginForm.serializeForm();
        if (loginForm.validate()) {
            store.dispatch(userActions.set({
                username: formData.username,
                email: formData.email
            }));
            this.shadowRoot.querySelector('paper-dialog').close();
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
        let msgForm = this.shadowRoot.querySelector('#message-form');
        let formData = msgForm.serializeForm();
        this.dispatchEvent(new CustomEvent('send-message',
            {
                detail: {
                    message: {
                        text: formData.message,
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
