Polymer({
    is: 'channelstream-connection',

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

    properties: {
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
    },

    /**
     * Mutators hold functions that you can set locally to change the data
     * that the client is sending to all endpoints
     * you can call it like `elem.mutators('connect', yourFunc())`
     * mutators will be executed in order they were pushed onto arrays
     *
     */
    mutators: {
        connect: function () {
            return [];
        }(),
        message: function () {
            return [];
        }(),
        subscribe: function () {
            return [];
        }(),
        unsubscribe: function () {
            return [];
        }(),
        disconnect: function () {
            return [];
        }(),
        userState: function () {
            return [];
        }()
    },
    ready: function () {
        this.isReady = true;
    },
    created: function () {
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
    },

    /**
     * Connects user and fetches connection id from the server.
     *
     */
    connect: function () {
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
        this.connection.listenOpenedCallback = this._listenOpenedCallback.bind(this)
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

    },
    /**
     * Overwrite with custom function that will
     */
    addMutator: function (type, func) {
        this.connection.addMutator(type, func);
    },
    /**
     * Updates user state.
     *
     */
    updateUserState: function (stateObj) {
        this.connection.updateUserState(stateObj);
    },
    /**
     * Subscribes user to channels.
     *
     */
    subscribe: function (channels) {
        this.connection.subscribe(channels);
    },
    /**
     * Unsubscribes user from channels.
     *
     */
    unsubscribe: function (unsubscribe) {
        this.connection.unsubscribe(unsubscribe);
    },

    /**
     * calculates list of channels we should add user to based on difference
     * between channels property and passed channel list
     */
    calculateSubscribe: function (channels) {
        return this.connection.calculateSubscribe(channels);
    },
    /**
     * calculates list of channels we should remove user from based difference
     * between channels property and passed channel list
     */
    calculateUnsubscribe: function (channels) {
        return this.connection.calculateUnsubscribe(channels);
    },
    /**
     * Marks the connection as expired.
     *
     */
    disconnect: function () {
        return this.connection.disconnect();
    },

    /**
     * Sends a message to the server.
     *
     */
    message: function (message) {
        return this.connection.message(message);
    },


    _channelsChangedCallback: function (channels) {
        // do not fire the event if set() didn't mutate anything
        // is this a reliable way to do it?
        if (!this.isReady || event === undefined) {
            return;
        }
        this.fire('channelstream-channels-changed', this.connection.channels);
    },

    _listenOpenedCallback: function (request, data) {
        this.connected = this.connection.connected;
        this.fire('channelstream-listen-opened', request);
    },
    _connectErrorCallback: function (request, data) {
        this.connected = this.connection.connected;
        this.fire('channelstream-connect-error', request);
    },

    _listenMessageCallback: function (message) {
        this.fire('channelstream-listen-message', message);

    },

    _handleWebsocketCloseEvent: function (event) {
        this.connected = this.connection.connected;
        this.fire('channelstream-websocket-closed', event.detail);
    },

    _listenErrorCallback: function (request, data) {
        this.connected = this.connection.connected;
        this.fire('channelstream-listen-error', request);
    },

    _connectCallback: function (request, data) {
        this.connectionId = this.connection.connectionId;
        this.fire('channelstream-connected', data);
    },

    _disconnectCallback: function (request, data) {
        this.connected = this.connection.connected;
        this.fire('channelstream-disconnected', request);
    },

    _messageCallback: function (request, data) {
        this.fire('channelstream-message-sent', data);
    },
    _messageErrorCallback: function (request, data) {
        this.fire('channelstream-message-error', request);
    },

    _subscribeCallback: function (request, data) {
        this.fire('channelstream-subscribed', data);
    },

    _subscribeErrorCallback: function (request, data) {
        this.fire('channelstream-subscribe-error', request);
    },

    _unsubscribeCallback: function (request, data) {
        this.fire('channelstream-unsubscribed', data);
    },

    _unsubscribeErrorCallback: function (request, data) {
        this.fire('channelstream-unsubscribe-error', request);
    },

    _setUserStateCallback: function (request, data) {
        this.fire('channelstream-set-user-state', data);
    },

    _setUserStateErrorCallback: function (request, data) {
        this.fire('channelstream-set-user-state-error', request);
    },

    testEvent: function (ev) {
        console.log('testEvent', ev.type, ev.detail);
    }
});
