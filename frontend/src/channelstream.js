(function () {
    'use strict';

    function ChannelStreamRequest() {
        this.headers = [];
        this.body = null;
        this.url = '';
        this.request = null;
        this.handleError = function (request, respText) {
            console.error('request', request);
            console.error('respText', respText);
        };
        this.handleResponse = function (request, respText) {
            console.info('request', request);
            console.info('respText', respText);
        };
        this.handleStateChange = function () {
            var result = this.request.responseText;
            try {
                result = JSON.parse(result);
            } catch (exc) {

            }
            if (this.request.readyState === XMLHttpRequest.DONE) {
                if (this.request.status <= 400) {
                    this.handleResponse(this.request, result);
                } else {
                    this.handleError(this.request, result);
                }
            }
        };
        this.execute = function () {
            this.request = new XMLHttpRequest();
            this.request.onreadystatechange = this.handleStateChange.bind(this);
            if (this.headers) {
                for (var i = 0; i < this.headers.length; i++) {
                    request.setRequestHeader(this.headers[i].name, headers[i].value);
                }
            }
            if (this.body) {
                this.request.open('POST', this.url);
                this.request.setRequestHeader('Content-Type', 'application/json');
                this.request.send(JSON.stringify(this.body));
            }
            else {
                this.request.open(this.type, this.url);
            }
        };
    };

    var ChannelStreamConnection = {
        debug: false,

        /** List of channels user should be subscribed to. */
        channels: [],
        /** Username of connecting user. */
        username: 'Anonymous',
        /** Connection identifier. */
        connectionId: null,
        /** Websocket instance. */
        websocket: null,
        /** Websocket connection url. */
        websocketUrl: '',
        /** URL used in `connect()`. */
        connectUrl: '',
        /** URL used in `disconnect()`. */
        disconnectUrl: '',
        /** URL used in `subscribe()`. */
        subscribeUrl: '',
        /** URL used in `unsubscribe()`. */
        unsubscribeUrl: '',
        /** URL used in `updateUserState()`. */
        userStateUrl: '',
        /** URL used in `message()`. */
        messageUrl: '',
        /** Long-polling connection url. */
        longPollUrl: '',
        /** Long-polling connection url. */
        shouldReconnect: true,
        /** Should send heartbeats. */
        heartbeats: true,
        /** How much should every retry interval increase (in milliseconds) */
        increaseBounceIv: 2000,
        _currentBounceIv: 0,
        /** Should use websockets or long-polling by default */
        noWebsocket: false,
        connected: false,

        /**
         * Mutators hold functions that you can set locally to change the data
         * that the client is sending to all endpoints
         * you can call it like `elem.mutators('connect', yourFunc())`
         * mutators will be executed in order they were pushed onto arrays
         *
         */
        mutators: {
            connect: [],
            message: [],
            subscribe: [],
            unsubscribe: [],
            disconnect: [],
            userState: []
        },

        /**
         * Connects user and fetches connection id from the server.
         *
         */
        connect: function () {
            var request = new ChannelStreamRequest();
            request.url = this.connectUrl;
            request.body = {
                username: this.username,
                channels: this.channels
            };
            for (var i = 0; i < this.mutators.connect.length; i++) {
                this.mutators.connect[i](request);
            }
            request.handleError = this._handleConnectError.bind(this);
            request.handleResponse = this._handleConnect.bind(this);
            request.execute();
        },
        /**
         * add custom function that will manipulate request before its being executed
         */
        addMutator: function (type, func) {
            this.mutators[type].push(func);
        },
        /**
         * Updates user state.
         *
         */
        updateUserState: function (stateObj) {
            var request = new ChannelStreamRequest();
            request.url = this.userStateUrl;
            request.body = {
                username: this.username,
                conn_id: this.connectionId,
                update_state: stateObj
            };
            for (var i = 0; i < this.mutators.userState.length; i++) {
                this.mutators.userState[i](request);
            }
            request.handleError = this._handleSetUserStateError.bind(this);
            request.handleResponse = this._handleSetUserState.bind(this);
            request.execute();
        },
        /**
         * Subscribes user to channels.
         *
         */
        subscribe: function (channels) {
            var request = new ChannelStreamRequest();
            request.url = this.subscribeUrl;
            request.body = {
                channels: channels,
                conn_id: this.connectionId
            };
            for (var i = 0; i < this.mutators.subscribe.length; i++) {
                this.mutators.subscribe[i](request);
            }
            request.handleError = this._handleSubscribe.bind(this);
            request.handleResponse = this._handleSubscribeError.bind(this);
            if (request.body.channels.length) {
                request.execute();
            }
        },
        /**
         * Unsubscribes user from channels.
         *
         */
        unsubscribe: function (unsubscribe) {
            var request = new ChannelStreamRequest();
            request.url = this.unsubscribeUrl;
            request.body = {
                channels: unsubscribe,
                conn_id: this.connectionId
            };
            for (var i = 0; i < this.mutators.unsubscribe.length; i++) {
                this.mutators.unsubscribe[i](request);
            }
            request.handleError = this._handleUnsubscribeError.bind(this);
            request.handleResponse = this._handleUnsubscribe.bind(this);
            request.execute();
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
            var request = new ChannelStreamRequest();
            request.url = this.disconnectUrl;
            request.body = {
                conn_id: this.connectionId
            };
            for (var i = 0; i < this.mutators.disconnect.length; i++) {
                this.mutators.disconnect[i](request);
            }
            request.handleResponse = this._handleDisconnect.bind(this);
            request.execute();
            this.closeConnection();
        },

        /**
         * Sends a message to the server.
         *
         */
        message: function (message) {
            var request = new ChannelStreamRequest();
            request.url = this.messageUrl;
            request.body = messageUrl;
            for (var i = 0; i < this.mutators.message.length; i++) {
                this.mutators.message[i](request);
            }
            request.handleError = this._handleMessageError.bind(this);
            request.handleResponse = this._handleMessage.bind(this);
            request.execute();
        },
        /**
         * Opens "long lived" (websocket/longpoll) connection to the channelstream server.
         *
         */
        startListening: function (request, data) {
            this.startListeningCallback(request, data);
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

        startListeningCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('startListeningCallback', request, data);
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
            var request = new ChannelStreamRequest();
            request.url = this.longPollUrl + '?conn_id=' + this.connectionId;
            request.handleError = this._handleListenErrorEvent.bind(this);
            request.handleResponse = function(request, data){
                this._handleListenMessageEvent(data);
            }.bind(this)
            request.execute();
            this._ajaxListen = request;
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
            var request = this._ajaxListen.request;
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.onclose = null;
                this.websocket.onerror = null;
                this.websocket.close();
            }
            request.abort();
            this.connected = false;
            this.connectionClosedCallback();
        },

        connectionClosedCallback: function () {
            if (!this.debug) {
                return
            }
            console.log('connectionClosedCallback');
        },

        channelsChangedCallback: function (data) {
            if (!this.debug) {
                return
            }
            console.log('channelsChangedCallback', data);
        },


        _handleListenOpen: function (request, data) {
            this.connected = true;
            this.listenOpenedCallback(request, data);
            this.createHeartBeats();
        },

        listenOpenedCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('listenOpenedCallback', request, data);
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

        _handleListenError: function (request, data) {
            this.connected = false;
            this.retryConnection(request, data);
        },
        _handleConnectError: function (request, data) {
            this.connected = false;
            this.retryConnection(request, data);
            this.connectErrorCallback(request, data);
        },

        connectErrorCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('connectErrorCallback', request, data);
        },

        _handleListenMessageEvent: function (data) {
            var parsedData = null;
            // comes from iron-ajax
            if (data) {
                parsedData = JSON.parse(data.data);
                // comes from websocket
                setTimeout(this.openLongPoll.bind(this), 0);
            } else {
                parsedData = JSON.parse(data);
            }
            this.listenMessageCallback(parsedData);

        },

        listenMessageCallback: function (data) {
            if (!this.debug) {
                return
            }
            console.log('listenMessageCallback', data)
        },

        _handleListenCloseEvent: function (request, data) {
            this.connected = false;
            this.listenCloseCallback(request, data);
            this.retryConnection();
        },

        listenCloseCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('listenCloseCallback', request, data)
        },

        _handleListenErrorEvent: function (request, data) {
            this.connected = false;
            this.listenErrorCallback(request, data);
        },

        listenErrorCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('listenErrorCallback', request, data)
        },

        _handleConnect: function (request, data) {
            this.currentBounceIv = 0;
            this.connectionId = data.conn_id;
            this.startListening(request, data);
            this.connectedCallback(request, data);
        },

        connectedCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('connectedCallback', request, data)
        },

        _handleDisconnect: function (request, data) {
            this.connected = false;
            this.disconnectedCallback(request, data);
        },

        disconnectedCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('disconnectedCallback', request, data)
        },

        _handleMessage: function (request, data) {
            this.messageCallback(request, data);
        },

        messageCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('messageCallback', request, data)
        },

        _handleMessageError: function (request, data) {
            this.messageErrorCallback(request, data);
        },

        messageErrorCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('messageErrorCallback', request, data)
        },

        _handleSubscribe: function (request, data) {
            this.subscribeCallback(request, data);
        },

        subscribeCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('subscribeCallback', request, data)
        },

        _handleSubscribeError: function (request, data) {
            this.subscribeErrorCallback(request, data);
        },

        subscribeErrorCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('subscribeErrorCallback', request, data)
        },

        _handleUnsubscribe: function (request, data) {
            this.unsubscribeCallback(request, data);
        },

        unsubscribeCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('unsubscribeCallback', request, data)
        },

        _handleUnsubscribeError: function (request, data) {
            this.unsubscribeErrorCallback(request, data);
        },

        unsubscribeErrorCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('unsubscribeErrorCallback', request, data)
        },

        _handleSetUserState: function (request, data) {
            this.setUserStateCallback(request, data);
        },

        setUserStateCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('setUserStateCallback', request, data)
        },

        _handleSetUserStateError: function (request, data) {
            this.setUserStateErrorCallback(request, data);
        },

        setUserStateErrorCallback: function (request, data) {
            if (!this.debug) {
                return
            }
            console.log('setUserStateErrorCallback', request, data)
        },
    };
    window.ChannelStreamConnection = ChannelStreamConnection;

})();
