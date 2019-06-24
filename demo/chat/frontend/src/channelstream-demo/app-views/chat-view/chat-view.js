import {LitElement, html} from 'lit-element';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../redux/store.js';

import 'weightless/tab-group/tab-group.js';
import 'weightless/tab/tab.js';
import 'weightless/button/button.js';
import 'weightless/icon/icon.js';
import 'weightless/dialog/dialog.js';
import 'weightless/textfield/textfield.js';
import '@material/mwc-icon/mwc-icon.js';
import '@material/mwc-button/mwc-button.js';

import './chat-message-list/chat-message-list.js';
import './chat-channel-picker/chat-channel-picker.js';
import './chat-user-list/chat-user-list.js';
import './chat-status-selector/chat-status-selector.js';

import {actions as userActions} from '../../redux/user';
import {actions as channelViewUiActions} from '../../redux/chat_view/ui';

class ChatView extends connect(store)(LitElement) {


    render() {

        let dialogButton = null;
        if (this.user.anonymous) {
            dialogButton = html`
                <mwc-button @click=${(e) => this.openDialog(e)} raised>
                <mwc-icon>account_box</mwc-icon>
                Change username
                </mwc-button>
            `
        }

        return html`
            <style>
            * {
                box-sizing: border-box;
                --button-bg: var(--mdc-theme-primary);
            }

            #vertical-holder{
                display: flex;
                flex-direction: column;
            }

            #column-holder{
                display: flex;
                height: calc(100vh - 300px);
            }

            #bottom-holder{
                margin-top: 5px;
            }

            :host > *{

            }
            .right-column {
                width: 250px;
                margin-left: 30px;
            }

            .left-column {
                flex-grow: 1;
                overflow: auto;
            }

            #message-input {
                display: inline-block;
                min-width: 50%;
            }
        </style>

        <wl-dialog fixed backdrop id="loginDialog">
           <p slot="header">Change your username</p>
           <div slot="content">
                <form method="post" id="login-form" enctype="multipart/form-data">
                    <wl-textfield label="User Name" name="username" min-length="1" auto-validate required></wl-textfield>
                    <wl-textfield label="Email" name="email" min-length="1" auto-validate required></wl-textfield>
                </form>
           </div>
           <div slot="footer">
              <mwc-button @click=${(e) => this.changeUser(e)} autofocus>Confirm credentials</mwc-button>
           </div>
        </wl-dialog>

        <div id="vertical-holder">
                <wl-tab-group>
                    ${this.user.subscribedChannels.map((channel) => html`
                    <wl-tab @click=${(e) => this.selectChannel(channel)} ?checked=${this.selectedChannel == channel}>
                            Channel: ${channel}
                    </wl-tab>
                    `)}
                </wl-tab-group>

        <div id="column-holder">
                <chat-message-list class="left-column"></chat-message-list>
            <div class="right-column">
                <chat-status-selector></chat-status-selector>
                <chat-user-list .selectedChannel=${this.selectedChannel}></chat-user-list>
            </div>
        </div>

        <form method="post" id="message-form" enctype="multipart/form-data">
            <wl-textfield id="message-input" name="message" label="Your message"></wl-textfield>
            <wl-button fab flat inverted @click=${(e) => this.messageSend(e)} style="vertical-align: middle;">
               <wl-icon>send</wl-icon>
            </wl-button>
        </form>

        <div id="bottom-holder">
        ${dialogButton}
        <chat-channel-picker .subscribedChannels=${this.user.subscribedChannels}
                             .possibleChannels=${this.possibleChannels}></chat-channel-picker>
        </div>
        </div>
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

    stateChanged(state) {
        this.user = state.user;
        this.channels = state.chatView.channels;
        this.possibleChannels = state.chatView.ui.possibleChannels;
        this.selectedChannel = state.chatView.ui.selectedChannel;
        this.user = state.user;
        this.users = state.chatView.users;
    }

    constructor() {
        super();
        this.selectedChannel = 'pub_chan';
    }

    selectChannel(channelName) {
        console.log('selectChannel', channelName);
        store.dispatch(channelViewUiActions.setViewedChannel(channelName));
    }

    loadHistory(messageList, channel) {
        this.set(['messages', channel], messageList);
    }

    openDialog() {
        this.shadowRoot.querySelector('wl-dialog').show();
    }

    changeUser(event) {
        event.preventDefault();
        let loginForm = this.shadowRoot.querySelector('#login-form');
        let formData = new FormData(loginForm);
        if (loginForm.checkValidity()) {
            store.dispatch(userActions.set({
                username: formData.get('username'),
                email: formData.get('email')
            }));
            this.shadowRoot.querySelector('wl-dialog').open = false;
        }
    }

    /** stop default form submit because shady dom might fire it twice */
    formPresubmit(event) {
        event.preventDefault();
    }

    /** sends the signal that will pass the message to the
     * channelstream-connection element */
    messageSend(event) {
        event.preventDefault();
        let msgForm = this.shadowRoot.querySelector('#message-form');
        let formData = new FormData(msgForm)
        this.dispatchEvent(new CustomEvent('message-send',
            {
                detail: {
                    message: {
                        text: formData.get('message'),
                        email: this.user.email,
                    },
                    channel: this.selectedChannel,
                    user: this.user.username,
                },
                composed: true, bubbles: true
            }));
        this.shadowRoot.querySelector('#message-form wl-textfield').value = '';
    }
}

customElements.define(ChatView.is, ChatView);
