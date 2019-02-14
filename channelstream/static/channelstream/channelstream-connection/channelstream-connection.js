import {ChannelStreamConnection} from '../channelstream.js';

/**
 *
 `<channelstream-connection>` allows you to connect and interact with channelstream server
 abstracting websocket/long-polling connections from you.

 In typical use, just slap some `<channelstream-connection>` at the top of your body:

 <body>
 <channelstream-connection
 username="{{user.username}}"
 connect-url="http://127.0.0.1:8000/demo/connect"
 disconnect-url="http://127.0.0.1:8000/disconnect"
 subscribe-url="http://127.0.0.1:8000/demo/subscribe"
 message-url="http://127.0.0.1:8000/demo/message"
 message-edit-url="http://127.0.0.1:8000/demo/edit"
 message-delete-url="http://127.0.0.1:8000/demo/delete"
 long-poll-url="http://127.0.0.1:8000/listen"
 websocket-url="http://127.0.0.1:8000/ws"
 channels-url='["channel1", "channel2"]' />

 Then you can do `channelstreamElem.connect()` to kick off your connection.
 This element also handles automatic reconnections.

 ## Default handlers

 By default element has a listener attached that will fire `startListening()` handler on `channelstream-connected` event.

 By default element has a listener attached that will fire `retryConnection()` handler on `channelstream-connect-error` event,
 this handler will forever try to re-establish connection to the server incrementing intervals between retries up to 1 minute.
 */
export class ChannelStreamConnectionElement extends HTMLElement {

    static get version() {
        return '0.0.2';
    }

    static get is() {
        return 'channelstream-connection';
    }

    /**
     * Fired when `channels` array changes.
     *
     * @event channelstream-channels-changed
     */

    /**
     * Fired when `connect()` method succeeds.
     *
     * @event channelstream-connected
     */

    /**
     * Fired when `connect` fails.
     *
     * @event channelstream-connect-error
     */

    /**
     * Fired when `disconnect()` succeeds.
     *
     * @event channelstream-disconnected
     */

    /**
     * Fired when `message()` succeeds.
     *
     * @event channelstream-message-sent
     */

    /**
     * Fired when `message()` fails.
     *
     * @event channelstream-message-error
     */

    /**
     * Fired when `subscribe()` succeeds.
     *
     * @event channelstream-subscribed
     */

    /**
     * Fired when `subscribe()` fails.
     *
     * @event channelstream-subscribe-error
     */

    /**
     * Fired when `unsubscribe()` succeeds.
     *
     * @event channelstream-unsubscribed
     */

    /**
     * Fired when `unsubscribe()` fails.
     *
     * @event channelstream-unsubscribe-error
     */

    /**
     * Fired when `setUserState()` succeeds.
     *
     * @event channelstream-set-user-state
     */

    /**
     * Fired when `setUserState()` fails.
     *
     * @event channelstream-set-user-state-error
     */


    /**
     * Fired when listening connection receives a message.
     *
     * @event channelstream-listen-message
     */

    /**
     * Fired when listening connection is opened.
     *
     * @event channelstream-listen-opened
     */

    /**
     * Fired when listening connection is closed.
     *
     * @event channelstream-websocket-closed
     */

    /**
     * Fired when listening connection suffers an error.
     *
     * @event channelstream-listen-error
     */

    static get observedAttributes() {
        return ['channels'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        this.dispatchEvent(new CustomEvent('channels-changed', {
            detail: {value: this.channels},
            bubbles: true,
            composed: true
        }));
    }

    constructor() {
        super();
        /**
         * Mutators hold functions that you can set locally to change the data
         * that the client is sending to all endpoints
         * you can call it like `elem.mutators('connect', yourFunc())`
         * mutators will be executed in order they were pushed onto arrays
         *
         */
        this.mutators = {
            connect: [],
            message: [],
            messageEdit: [],
            messageDelete: [],
            subscribe: [],
            unsubscribe: [],
            disconnect: [],
            userState: []
        };

        this.isReady = false;
        this.username = 'Anonymous';
        this.connectionId = '';
        this.websocketUrl = '';
        this.connectUrl = '';
        this.disconnectUrl = '';
        this.subscribeUrl = '';
        this.unsubscribeUrl = '';
        this.userStateUrl = '';
        this.messageUrl = '';
        this.messageEditUrl = '';
        this.messageDeleteUrl = '';
        this.longPollUrl = '';
        this.shouldReconnect = true;
        this.heartbeats = true;
        this.increaseBounceIv = 2000;
        this.noWebsocket = false;
        this.connected = false;
        this.connection = new ChannelStreamConnection();
    }


    ready() {
        this.isReady = true;
    }

    // connectedCallback() {
    //     super.connectedCallback();
    //     this.addEventListener('channelstream-channels-changed', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-connected', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-connect-error', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-disconnected', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-message-sent', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-message-error', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-subscribed', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-subscribe-error', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-unsubscribed', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-unsubscribe-error', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-listen-message', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-listen-opened', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-websocket-closed', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-listen-error', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-set-user-state', this.testEvent.bind(this));
    //     this.addEventListener('channelstream-set-user-state-error', this.testEvent.bind(this));
    // }

    /**
     * Connects user and fetches connection id from the server.
     *
     */
    connect() {
        this.connection.url = this.connectUrl;
        this.connection.connectUrl = this.connectUrl;
        this.connection.disconnectUrl = this.disconnectUrl;
        this.connection.subscribeUrl = this.subscribeUrl;
        this.connection.unsubscribeUrl = this.unsubscribeUrl;
        this.connection.messageUrl = this.messageUrl;
        this.connection.messageEditUrl = this.messageEditUrl;
        this.connection.messageDeleteUrl = this.messageDeleteUrl;
        this.connection.longPollUrl = this.longPollUrl;
        this.connection.websocketUrl = this.websocketUrl;
        this.connection.userStateUrl = this.userStateUrl;
        this.connection.channels = this.channels;
        this.connection.noWebsocket = this.noWebsocket;
        this.connection.username = this.username;
        this.connection.channelsChangedCallback = this._channelsChangedCallback.bind(this);
        this.connection.connectCallback = this._connectCallback.bind(this);
        // this.connection.connectErrorCallback = this._connectErrorCallback.bind(this);
        this.connection.disconnectCallback = this._disconnectCallback.bind(this);
        //this.connection.listenCloseCallback
        this.connection.listenErrorCallback = this._listenErrorCallback.bind(this);
        this.connection.listenMessageCallback = this._listenMessageCallback.bind(this);
        this.connection.listenOpenedCallback = this._listenOpenedCallback.bind(this);
        this.connection.messageCallback = this._messageCallback.bind(this);
        this.connection.messageErrorCallback = this._messageErrorCallback.bind(this);
        this.connection.messageEditCallback = this._messageEditCallback.bind(this);
        this.connection.messageEditErrorCallback = this._messageEditErrorCallback.bind(this);
        this.connection.messageDeleteCallback = this._messageDeleteCallback.bind(this);
        this.connection.messageDeleteErrorCallback = this._messageDeleteErrorCallback.bind(this);
        this.connection.setUserStateCallback = this._setUserStateCallback.bind(this);
        this.connection.setUserStateErrorCallback = this._setUserStateErrorCallback.bind(this);
        //this.connection.startListeningCallback
        this.connection.subscribeCallback = this._subscribeCallback.bind(this);
        this.connection.subscribeErrorCallback = this._subscribeErrorCallback.bind(this);
        this.connection.unsubscribeCallback = this._unsubscribeCallback.bind(this);
        this.connection.unsubscribeErrorCallback = this._unsubscribeErrorCallback.bind(this);
        this.connection.connect();
    }

    /**
     * Overwrite with custom function that will
     */
    addMutator(type, func) {
        this.connection.addMutator(type, func);
    }

    /**
     * Updates user state.
     *
     */
    updateUserState(stateObj) {
        this.connection.updateUserState(stateObj);
    }

    /**
     * Subscribes user to channels.
     *
     */
    subscribe(channels) {
        this.connection.subscribe(channels);
    }

    /**
     * Unsubscribes user from channels.
     *
     */
    unsubscribe(unsubscribe) {
        this.connection.unsubscribe(unsubscribe);
    }

    /**
     * calculates list of channels we should add user to based on difference
     * between channels property and passed channel list
     */
    calculateSubscribe(channels) {
        return this.connection.calculateSubscribe(channels);
    }

    /**
     * calculates list of channels we should remove user from based difference
     * between channels property and passed channel list
     */
    calculateUnsubscribe(channels) {
        return this.connection.calculateUnsubscribe(channels);
    }

    /**
     * Marks the connection as expired.
     *
     */
    disconnect() {
        return this.connection.disconnect();
    }

    /**
     * Send a message to the backend.
     *
     */
    message(message) {
        return this.connection.message(message);
    }

    /**
     * Edit a message in channelstream.
     *
     */
    edit(message) {
        return this.connection.edit(message);
    }

    /**
     * Delete a message in channelstream.
     *
     */
    delete(message) {
        return this.connection.delete(message);
    }

    _channelsChangedCallback(channels) {
        // do not fire the event if set() didn't mutate anything
        // is this a reliable way to do it?
        if (!this.isReady || event === undefined) {
            return;
        }
        this.dispatchEvent(new CustomEvent('channelstream-channels-changed', {
            detail: {channels: this.connection.channels},
            bubbles: true,
            composed: true
        }));
    }

    _listenOpenedCallback(request, data) {
        this.connected = this.connection.connected;
        this.dispatchEvent(new CustomEvent('channelstream-listen-opened', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _connectErrorCallback(request, data) {
        this.connected = this.connection.connected;
        this.dispatchEvent(new CustomEvent('channelstream-connect-error', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _listenMessageCallback(messages) {
        this.dispatchEvent(new CustomEvent('channelstream-listen-message', {
            detail: {messages: messages},
            bubbles: true,
            composed: true
        }));
    }

    _handleWebsocketCloseEvent(event) {
        this.connected = this.connection.connected;
        this.dispatchEvent(new CustomEvent('channelstream-websocket-closed', {
            detail: event.detail,
            bubbles: true,
            composed: true
        }));
    }

    _listenErrorCallback(request, data) {
        this.connected = this.connection.connected;
        this.dispatchEvent(new CustomEvent('channelstream-listen-error', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _connectCallback(request, data) {
        this.connectionId = this.connection.connectionId;
        this.dispatchEvent(new CustomEvent('channelstream-connected', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _disconnectCallback(request, data) {
        this.connected = this.connection.connected;
        this.dispatchEvent(new CustomEvent('channelstream-disconnected', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _messageCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-message-sent', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _messageErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-message-error', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _messageEditCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-message-edit-sent', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _messageEditErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-message-edit-error', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _messageDeleteCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-message-delete-sent', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _messageDeleteErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-message-delete-error', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _subscribeCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-subscribed', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _subscribeErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-subscribe-error', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _unsubscribeCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-unsubscribed', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _unsubscribeErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-unsubscribe-error', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _setUserStateCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-set-user-state', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    _setUserStateErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-set-user-state-error', {
            detail: {request: request, data: data},
            bubbles: true,
            composed: true
        }));
    }

    testEvent(ev) {
        console.log('testEvent', ev.type, ev.detail);
    }
}


customElements.define(ChannelStreamConnectionElement.is,
    ChannelStreamConnectionElement);
