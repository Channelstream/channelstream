import {PolymerElement} from '@polymer/polymer/polymer-element.js'
import '../../channelstream.js';

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
class ChannelStreamConnection extends PolymerElement {
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

    static get properties() {
        return {
            isReady: Boolean,
            /** List of channels user should be subscribed to. */
            channels: {
                type: Array,
                value: function () {
                    return [];
                },
                notify: true
            },
            /** Username of connecting user. */
            username: {
                type: String,
                value: 'Anonymous',
                reflectToAttribute: true
            },
            /** Connection identifier. */
            connectionId: {
                type: String,
                reflectToAttribute: true
            },
            /** Websocket connection url. */
            websocketUrl: {
                type: String,
                value: ''
            },
            /** URL used in `connect()`. */
            connectUrl: {
                type: String,
                value: ''
            },
            /** URL used in `disconnect()`. */
            disconnectUrl: {
                type: String,
                value: ''
            },
            /** URL used in `subscribe()`. */
            subscribeUrl: {
                type: String,
                value: ''
            },
            /** URL used in `unsubscribe()`. */
            unsubscribeUrl: {
                type: String,
                value: ''
            },
            /** URL used in `updateUserState()`. */
            userStateUrl: {
                type: String,
                value: ''
            },
            /** URL used in `message()`. */
            messageUrl: {
                type: String,
                value: ''
            },
            /** Long-polling connection url. */
            longPollUrl: {
                type: String,
                value: ''
            },
            /** Long-polling connection url. */
            shouldReconnect: {
                type: Boolean,
                value: true
            },
            /** Should send heartbeats. */
            heartbeats: {
                type: Boolean,
                value: true
            },
            /** How much should every retry interval increase (in milliseconds) */
            increaseBounceIv: {
                type: Number,
                value: 2000
            },
            /** Should use websockets or long-polling by default */
            noWebsocket: {
                type: Boolean,
                reflectToAttribute: true,
                value: false
            },
            connected: {
                type: Boolean,
                reflectToAttribute: true,
                value: false
            },
            connection: {
                type: Object,
                value: function () {
                    return window.ChannelStreamConnection;
                }
            }
        };
    }

    constructor(){
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
            subscribe: [],
            unsubscribe: [],
            disconnect: [],
            userState: []
        };
    }



    ready() {
        this.isReady = true;
    }

    created() {
        this.listen(this, 'channelstream-channels-changed', 'testEvent');
        this.listen(this, 'channelstream-connected', 'testEvent');
        this.listen(this, 'channelstream-connect-error', 'testEvent');
        this.listen(this, 'channelstream-disconnected', 'testEvent');
        this.listen(this, 'channelstream-message-sent', 'testEvent');
        this.listen(this, 'channelstream-message-error', 'testEvent');
        this.listen(this, 'channelstream-subscribed', 'testEvent');
        this.listen(this, 'channelstream-subscribe-error', 'testEvent');
        this.listen(this, 'channelstream-unsubscribed', 'testEvent');
        this.listen(this, 'channelstream-unsubscribe-error', 'testEvent');
        this.listen(this, 'channelstream-listen-message', 'testEvent');
        this.listen(this, 'channelstream-listen-opened', 'testEvent');
        this.listen(this, 'channelstream-websocket-closed', 'testEvent');
        this.listen(this, 'channelstream-listen-error', 'testEvent');
        this.listen(this, 'channelstream-set-user-state', 'testEvent');
        this.listen(this, 'channelstream-set-user-state-error', 'testEvent');
    }

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
        this.connection.longPollUrl = this.longPollUrl;
        this.connection.websocketUrl = this.websocketUrl;
        this.connection.userStateUrl = this.userStateUrl;
        this.connection.channels = this.channels;
        this.connection.noWebsocket = this.noWebsocket;
        this.connection.username = this.username;
        this.connection.channelsChangedCallback = this._channelsChangedCallback.bind(this);
        this.connection.connectCallback = this._connectCallback.bind(this);
        // this.connection.connectErrorCallback = this._connectErrorCallback.bind(this);
        //this.connection.connectionClosedCallback
        this.connection.disconnectCallback = this._disconnectCallback.bind(this);
        //this.connection.listenCloseCallback
        this.connection.listenErrorCallback = this._listenErrorCallback.bind(this);
        this.connection.listenMessageCallback = this._listenMessageCallback.bind(this);
        this.connection.listenOpenedCallback = this._listenOpenedCallback.bind(this);
        this.connection.messageCallback = this._messageCallback.bind(this);
        this.connection.messageErrorCallback = this._messageErrorCallback.bind(this);
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
     * Sends a message to the server.
     *
     */
    message(message) {
        return this.connection.message(message);
    }

    _channelsChangedCallback(channels) {
        // do not fire the event if set() didn't mutate anything
        // is this a reliable way to do it?
        if (!this.isReady || event === undefined) {
            return;
        }
        this.dispatchEvent(new CustomEvent('channelstream-channels-changed', {
            detail: {channels:this.connection.channels},
            bubbles: true,
            composed: true
        }));
    }

    _listenOpenedCallback(request, data) {
        this.connected = this.connection.connected;
        this.dispatchEvent(new CustomEvent('channelstream-listen-opened', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _connectErrorCallback(request, data) {
        this.connected = this.connection.connected;
        this.dispatchEvent(new CustomEvent('channelstream-connect-error', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _listenMessageCallback(messages) {
        this.dispatchEvent(new CustomEvent('channelstream-listen-message', {
            detail: {messages:messages},
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
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _connectCallback(request, data) {
        this.connectionId = this.connection.connectionId;
        this.dispatchEvent(new CustomEvent('channelstream-connected', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _disconnectCallback(request, data) {
        this.connected = this.connection.connected;
        this.dispatchEvent(new CustomEvent('channelstream-disconnected', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _messageCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-message-sent', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _messageErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-message-error', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _subscribeCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-subscribed', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _subscribeErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-subscribe-error', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _unsubscribeCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-unsubscribed', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _unsubscribeErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-unsubscribe-error', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _setUserStateCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-set-user-state', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    _setUserStateErrorCallback(request, data) {
        this.dispatchEvent(new CustomEvent('channelstream-set-user-state-error', {
            detail: {request:request, data:data},
            bubbles: true,
            composed: true
        }));
    }

    testEvent(ev) {
        console.log('testEvent', ev.type, ev.detail);
    }
}


customElements.define(ChannelStreamConnection.is, ChannelStreamConnection);
