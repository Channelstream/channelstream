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
     * @event channelstream-listen-closed
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
        /** Websocket instance. */
        websocket: {
            type: Object,
            value: null
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
        _currentBounceIv: {
            type: Number,
            reflectToAttribute: true,
            value: 0
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
        }
    },

    observers: [
        '_handleChannelsChange(channels.splices)'
    ],

    listeners: {
        'channelstream-connected': 'startListening',
        'channelstream-connect-error': 'retryConnection',
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
        this.listen(this, 'channelstream-listen-closed', 'testEvent');
        this.listen(this, 'channelstream-listen-error', 'testEvent');
        this.listen(this, 'channelstream-set-user-state', 'testEvent');
        this.listen(this, 'channelstream-set-user-state-error', 'testEvent');
    },

    /**
     * Connects user and fetches connection id from the server.
     *
     */
    connect: function () {
        var request = this.$['ajaxConnect'];
        request.url = this.connectUrl;
        request.body = {
            username: this.username,
            channels: this.channels
        };
        for (var i = 0; i < this.mutators.connect.length; i++) {
            this.mutators.connect[i](request);
        }
        request.generateRequest();
    },
    /**
     * Overwrite with custom function that will
     */
    addMutator: function (type, func) {
        this.mutators[type].push(func);
    },
    /**
     * Updates user state.
     *
     */
    updateUserState: function (stateObj) {
        var request = this.$['ajaxSetUserState'];
        request.url = this.userStateUrl;
        request.body = {
            username: this.username,
            conn_id: this.connectionId,
            update_state: stateObj
        };
        for (var i = 0; i < this.mutators.userState.length; i++) {
            this.mutators.userState[i](request);
        }
        request.generateRequest();
    },
    /**
     * Subscribes user to channels.
     *
     */
    subscribe: function (channels) {
        var request = this.$['ajaxSubscribe'];
        request.url = this.subscribeUrl;
        request.body = {
            channels: channels,
            conn_id: this.connectionId
        };
        for (var i = 0; i < this.mutators.subscribe.length; i++) {
            this.mutators.subscribe[i](request);
        }
        if (request.body.channels.length) {
            request.generateRequest();
        }
    },
    /**
     * Unsubscribes user from channels.
     *
     */
    unsubscribe: function (unsubscribe) {
        var request = this.$['ajaxUnsubscribe'];

        request.url = this.unsubscribeUrl;
        request.body = {
            channels: unsubscribe,
            conn_id: this.connectionId
        };
        for (var i = 0; i < this.mutators.unsubscribe.length; i++) {
            this.mutators.unsubscribe[i](request);
        }
        request.generateRequest();
    },

    /**
     * calculates list of channels we should add user to based on difference
     * between channels property and passed channel list
     */
    calculateSubscribe: function (channels) {
        var toSubscribe = [];
        for (var i = 0; i < channels.length; i++) {
            if (this.channels.indexOf(channels[i]) === -1) {
                toSubscribe.push(channels[i]);
            }
        }
        return toSubscribe;
    },
    /**
     * calculates list of channels we should remove user from based difference
     * between channels property and passed channel list
     */
    calculateUnsubscribe: function (channels) {
        var toUnsubscribe = [];
        for (var i = 0; i < channels.length; i++) {
            if (this.channels.indexOf(channels[i]) !== -1) {
                toUnsubscribe.push(channels[i]);
            }
        }
        return toUnsubscribe;
    },
    /**
     * Marks the connection as expired.
     *
     */
    disconnect: function () {
        var request = this.$['ajaxDisconnect'];
        request.url = this.disconnectUrl;
        request.params = {
            conn_id: this.connectionId
        };
        for (var i = 0; i < this.mutators.disconnect.length; i++) {
            this.mutators.disconnect[i](request);
        }
        // mark connection as expired
        request.generateRequest();
        // disconnect existing connection
        this.closeConnection();
    },

    /**
     * Sends a message to the server.
     *
     */
    message: function (message) {
        var request = this.$['ajaxMessage'];
        request.url = this.messageUrl;
        request.body = message;
        for (var i = 0; i < this.mutators.message.length; i++) {
            this.mutators.message[i](request);
        }
        request.generateRequest();
    },
    /**
     * Opens "long lived" (websocket/longpoll) connection to the channelstream server.
     *
     */
    startListening: function (event) {
        this.fire('start-listening', {});
        if (this.noWebsocket === false) {
            this.noWebsocket = !window.WebSocket;
        }
        if (this.noWebsocket === false) {
            this.openWebsocket();
        }
        else {
            this.openLongPoll();
        }
    },
    /**
     * Opens websocket connection.
     *
     */
    openWebsocket: function () {
        var url = this.websocketUrl + '?conn_id=' + this.connectionId;
        this.websocket = new WebSocket(url);
        this.websocket.onopen = this._handleListenOpen.bind(this);
        this.websocket.onclose = this._handleListenCloseEvent.bind(this);
        this.websocket.onerror = this._handleListenErrorEvent.bind(this);
        this.websocket.onmessage = this._handleListenMessageEvent.bind(this);
    },
    /**
     * Opens long-poll connection.
     *
     */
    openLongPoll: function () {
        var request = this.$['ajaxListen'];
        request.url = this.longPollUrl + '?conn_id=' + this.connectionId;
        request.generateRequest();
    },
    /**
     * Retries `connect()` call while incrementing interval between tries up to 1 minute.
     *
     */
    retryConnection: function () {
        if (!this.shouldReconnect) {
            return;
        }
        if (this._currentBounceIv < 60000) {
            this._currentBounceIv = this._currentBounceIv + this.increaseBounceIv;
        }
        else {
            this._currentBounceIv = 60000;
        }
        setTimeout(this.connect.bind(this), this._currentBounceIv);
    },
    /**
     * Closes listening connection.
     *
     */
    closeConnection: function () {
        var request = this.$['ajaxListen'];
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.onclose = null;
            this.websocket.onerror = null;
            this.websocket.close();
        }
        if (request.loading) {
            request.lastRequest.abort();
        }
        this.connected = false;
    },

    _handleChannelsChange: function (event) {
        // do not fire the event if set() didn't mutate anything
        // is this a reliable way to do it?
        if (!this.isReady || event === undefined) {
            return;
        }
        this.fire('channelstream-channels-changed', event);
    },

    _handleListenOpen: function (event) {
        this.connected = true;
        this.fire('channelstream-listen-opened', event);
        this.createHeartBeats();
    },

    createHeartBeats: function () {
        if (typeof this._heartbeat === 'undefined' && this.websocket !== null
            && this.heartbeats) {
            this._heartbeat = setInterval(this._sendHeartBeat.bind(this), 10000);
        }
    },

    _sendHeartBeat: function () {
        if (this.websocket.readyState === WebSocket.OPEN && this.heartbeats) {
            this.websocket.send(JSON.stringify({type: 'heartbeat'}));
        }
    },

    _handleListenError: function (event) {
        this.connected = false;
        this.retryConnection();
    },
    _handleConnectError: function (event) {
        this.connected = false;
        this.fire('channelstream-connect-error', event.detail);
    },

    _handleListenMessageEvent: function (event) {
        var data = null;
        // comes from iron-ajax
        if (event.detail) {
            data = JSON.parse(event.detail.response);
            // comes from websocket
            setTimeout(this.openLongPoll.bind(this), 0);
        } else {
            data = JSON.parse(event.data);
        }
        this.fire('channelstream-listen-message', data);

    },

    _handleListenCloseEvent: function (event) {
        this.connected = false;
        this.fire('channelstream-listen-closed', event.detail);
        this.retryConnection();
    },

    _handleListenErrorEvent: function (event) {
        this.connected = false;
        this.fire('channelstream-listen-error', {});
    },

    _handleConnect: function (event) {
        this.currentBounceIv = 0;
        this.connectionId = event.detail.response.conn_id;
        this.fire('channelstream-connected', event.detail.response);
    },

    _handleDisconnect: function (event) {
        this.connected = false;
        this.fire('channelstream-disconnected', {});
    },

    _handleMessage: function (event) {
        this.fire('channelstream-message-sent', event.detail.response);
    },
    _handleMessageError: function (event) {
        this.fire('channelstream-message-error', event.detail);
    },

    _handleSubscribe: function (event) {
        this.fire('channelstream-subscribed', event.detail.response);
    },

    _handleSubscribeError: function (event) {
        this.fire('channelstream-subscribe-error', event.detail);
    },

    _handleUnsubscribe: function (event) {
        this.fire('channelstream-unsubscribed', event.detail.response);
    },

    _handleUnsubscribeError: function (event) {
        this.fire('channelstream-unsubscribe-error', event.detail);
    },

    _handleSetUserState: function (event) {
        this.fire('channelstream-set-user-state', event.detail.response);
    },

    _handleSetUserStateError: function (event) {
        this.fire('channelstream-set-user-state-error', event.detail);
    },

    testEvent: function (event) {
        console.debug('launched', event.type, event.detail);
    }
});
