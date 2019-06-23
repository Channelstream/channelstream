import {LitElement, html} from 'lit-element';
import {connect} from 'pwa-helpers/connect-mixin.js';
import 'weightless/tab-group/tab-group.js';
import 'weightless/tab/tab.js';
import '@material/mwc-top-app-bar/mwc-top-app-bar.js';
import '../../../../../../frontend/src/debug.js';
import '@channelstream/channelstream';
import '../app-views/admin-view/admin-view.js';
import '../app-views/chat-view/chat-view.js';
import {store} from '../redux/store.js';
import {actions as appActions} from '../redux/app';
import {actions as userActions} from '../redux/user';
import {actions as chatViewChannelActions} from '../redux/chat_view/channels';
import {actions as chatViewUsersActions} from '../redux/chat_view/users';
import {actions as chatViewMessagesActions} from '../redux/chat_view/messages';

class ChannelStreamChatDemo extends connect(store)(LitElement) {

    render() {
        let currentPage;
        if (this.page === 'chat') {
            currentPage = html`<chat-view></chat-view>`
        }
        if (this.page === 'admin') {
            currentPage = html`<admin-view></admin-view>`
        }
        return html`
        <channelstream-connection
                id="channelstream-connection"
                .username=${this.user.username}
                .channels=${this.user.subscribedChannels}
                @channelstream-listen-message=${(e) => this.receivedMessage(e)}
                @channelstream-connected=${(e) => this.handleConnected(e)}
                @channelstream-subscribed=${(e) => this.handleSubscribed(e)}
                @channelstream-unsubscribed=${(e) => this.handleUnsubscribed(e)}
                @channelstream-channels-changed=${(e) => this.handleChannelsChange(e)}>
        </channelstream-connection>

        <mwc-top-app-bar type="fixed">
            <span slot="title" class="title">Channelstream Demo - Hello ${this.user.username}</span>


            <wl-tab-group slot="actionItems">
               <wl-tab @click=${(e) => this.switchTab("chat")} checked>Chat</wl-tab>
               <wl-tab @click=${(e) => this.switchTab("admin")}>Admin Stats</wl-tab>
            </wl-tab-group>

        </mwc-top-app-bar>

        <div class="pad-content">
            ${currentPage}
        </div>
        `
    }

    static get is() {
        return 'channelstream-chat-demo';
    }

    static get properties() {
        return {
            isReady: Boolean,
            user: Object,
            channels: Array,
            users: Object,
            page: String
        };
    }

    stateChanged(state) {
        let oldUser = this.user;
        this.user = state.user;
        this.channels = state.chatView.channels;
        this.users = state.chatView.users;
        this.page = state.app.selectedPage;
    }

    update(changedProps) {
        super.update();
        let changedUser = changedProps.get('user');
        if (changedUser && changedUser.username !== this.user.username) {
            this.handleUserChange();
        }
    }

    constructor() {
        super();
        this.appConfig = window.AppConf;
    }

    switchTab(tabName) {
        console.log('switchTab', tabName);
        store.dispatch(appActions.setPage(tabName));
    }

    receivedMessage(event) {
        for (let message of event.detail.messages) {
            // add message
            // console.info('message', message);
            if (message.type === 'message' || message.type === 'presence') {
                store.dispatch(chatViewMessagesActions.setChannelMessages([message]));
            }
            if (message.type === 'message:edit') {
                message.type = 'message';
                store.dispatch(chatViewMessagesActions.editChannelMessages([message]));
            }
            if (message.type === 'message:delete') {
                store.dispatch(chatViewMessagesActions.deleteChannelMessages([message.uuid]));
            }
            // update users on presence message
            if (message.type === 'presence') {
                // user joined
                if (message.message.action === 'joined') {
                    store.dispatch(chatViewUsersActions.setUserStates([{user: message.user, state: message.state}]));
                    store.dispatch(chatViewChannelActions.addChannelUsers(message.channel, [message.user]));
                }
                // user disconnected
                else {
                    store.dispatch(chatViewChannelActions.removeChannelUsers(message.channel, [message.user]));
                }
            }
            if (message.type === 'user_state_change') {
                store.dispatch(chatViewUsersActions.setUserStates([{
                    user: message.user,
                    state: message.message.state
                }]));
            }
        }
    }

    /** send the message via channelstream conn manager */
    messageSend(event) {
        this.getConnection().message(event.detail);
    }

    /** edit the message via channelstream conn manager */
    messageEdit(event) {
        this.getConnection().edit(event.detail);
    }

    /** delete the message via channelstream conn manager */
    messageDelete(event) {
        this.getConnection().delete(event.detail);
    }

    changeStatus(event) {
        var stateUpdates = event.detail;
        this.getConnection().updateUserState({user_state: stateUpdates});
    }

    /** kicks off the connection */
    firstUpdated() {
        var channelstreamConnection = this.querySelector('channelstream-connection');
        channelstreamConnection.connectUrl = this.appConfig.connectUrl;
        channelstreamConnection.disconnectUrl = this.appConfig.disconnectUrl;
        channelstreamConnection.subscribeUrl = this.appConfig.subscribeUrl;
        channelstreamConnection.unsubscribeUrl = this.appConfig.unsubscribeUrl;
        channelstreamConnection.messageUrl = this.appConfig.messageUrl;
        channelstreamConnection.messageEditUrl = this.appConfig.messageEditUrl;
        channelstreamConnection.messageDeleteUrl = this.appConfig.messageDeleteUrl;
        channelstreamConnection.longPollUrl = this.appConfig.longPollUrl;
        channelstreamConnection.websocketUrl = this.appConfig.websocketUrl;
        channelstreamConnection.userStateUrl = this.appConfig.userStateUrl;
        // enable for tests
        // channelstreamConnection.noWebsocket = true;

        // add a mutator for demo purposes - modify the request
        // to inject some state vars to connection json
        channelstreamConnection.addMutator('connect', function (request) {
            request.body.state = {email: this.user.email, status: 'ready'};
        }.bind(this));
        channelstreamConnection.connect();

        this.addEventListener('channelpicker-subscribe', this.subscribeToChannel);
        this.addEventListener('change-status', this.changeStatus);
        this.addEventListener('message-send', this.messageSend);
        this.addEventListener('message-edit', this.messageEdit);
        this.addEventListener('message-delete', this.messageDelete);
    }

    disconnectedCallback() {
        super.disconnectedCallback();
    }

    /** creates new connection on name change */
    handleUserChange() {
        var connection = this.getConnection();
        connection.disconnect();
        connection.connect();
    }

    /** subscribes/unsubscribes users from channels in channelstream */
    handleChannelsChange(e) {
        console.log('handleChannelsChange', e.detail);
        var connection = this.getConnection();
        var shouldUnsubscribe = connection.calculateUnsubscribe();
        if (shouldUnsubscribe.length > 0) {
            connection.unsubscribe(shouldUnsubscribe);
        } else {
            connection.subscribe();
        }
    }

    getConnection() {
        return this.querySelector('channelstream-connection');
    }

    handleConnected(event) {
        var data = event.detail.data;
        store.dispatch(userActions.setState(data.state));
        store.dispatch(userActions.setChannels(data.channels));
        store.dispatch(chatViewUsersActions.setUserStates(data.channels_info.users));
        store.dispatch(chatViewChannelActions.setChannelStates(data.channels_info.channels));
        for (let channel of Object.entries(data.channels_info.channels)) {
            store.dispatch(chatViewMessagesActions.setChannelMessages(channel[1].history));
        }
    }

    subscribeToChannel(event) {
        var connection = this.getConnection();
        var channel = event.detail.channel;
        var index = this.user.subscribedChannels.indexOf(channel);
        if (index !== -1) {
            var toUnsubscribe = connection.calculateUnsubscribe([channel]);
            connection.unsubscribe(toUnsubscribe);
        } else {
            var toSubscribe = connection.calculateSubscribe([channel]);
            connection.subscribe(toSubscribe);
        }
    }

    handleSubscribed(event) {
        console.log('handleSubscribed');
        var data = event.detail.data;
        var channelInfo = data.channels_info;
        store.dispatch(userActions.setChannels(data.channels));
        store.dispatch(chatViewUsersActions.setUserStates(channelInfo.users));
        store.dispatch(chatViewChannelActions.setChannelStates(channelInfo.channels));
        for (let channel of Object.entries(channelInfo.channels)) {
            store.dispatch(chatViewMessagesActions.setChannelMessages(channel[1].history));
        }
    }

    handleUnsubscribed(event) {
        var channelKeys = event.detail.data.unsubscribed_from;
        for (var i = 0; i < channelKeys.length; i++) {
            var key = channelKeys[i];
            store.dispatch(chatViewChannelActions.delChannelState(key));
        }
        store.dispatch(userActions.setChannels(event.detail.data.channels));
    }

    createRenderRoot() {
        /**
         * Render template in light DOM. Note that shadow DOM features like
         * encapsulated CSS are unavailable.
         */
        return this;
    }

}

customElements.define(ChannelStreamChatDemo.is, ChannelStreamChatDemo);
