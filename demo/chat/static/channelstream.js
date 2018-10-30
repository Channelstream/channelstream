/**
 * Main Channelstream connection class
 */
export class ChannelStreamConnection {

    constructor() {
        this.debug = false;

        /** List of channels user should be subscribed to. */
        this.channels = [];
        /** Username of connecting user. */
        this.username = 'Anonymous';
        /** Connection identifier. */
        this.connectionId = null;
        /** Websocket instance. */
        this.websocket = null;
        /** Websocket connection url. */
        this.websocketUrl = '';
        /** URL used in `connect()`. */
        this.connectUrl = '';
        /** URL used in `disconnect()`. */
        this.disconnectUrl = '';
        /** URL used in `subscribe()`. */
        this.subscribeUrl = '';
        /** URL used in `unsubscribe()`. */
        this.unsubscribeUrl = '';
        /** URL used in `updateUserState()`. */
        this.userStateUrl = '';
        /** URL used in `message()`. */
        this.messageUrl = '';
        /** URL used in `editMessage()`. */
        this.messageEditUrl = '';
        /** URL used in `deleteMessage()`. */
        this.messageDeleteUrl = '';
        /** Long-polling connection url. */
        this.longPollUrl = '';
        /** Long-polling connection url. */
        this.shouldReconnect = true;
        /** Should send heartbeats. */
        this.heartbeats = true;
        /** How much should every retry interval increase (in milliseconds) */
        this.increaseBounceIv = 2000;
        this._currentBounceIv = 0;
        /** Should use websockets or long-polling by default */
        this.noWebsocket = false;
        this.connected = false;

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
        }
    }

    /**
     * Sends AJAX call that creates user and fetches connection information
     * from the server.
     *
     */
    connect() {
        let request = new ChannelStreamRequest();
        request.url = this.connectUrl;
        request.body = {
            username: this.username,
            channels: this.channels
        };
        for (let callable of this.mutators.connect) {
            callable(request);
        }
        request.handleError = this._handleConnectError.bind(this);
        request.handleResponse = this._handleConnect.bind(this);
        request.execute();
    }

    /**
     *
     * Add custom function that will manipulate request before its being executed
     *
     * @param type {string} type of mutator function to register
     * @param func {function} a callable to register
     */
    addMutator(type, func) {
        this.mutators[type].push(func);
    }

    /**
     * Sends AJAX request to update user state.
     * @param stateObj {object}
     */
    updateUserState(stateObj) {
        let request = new ChannelStreamRequest();
        request.url = this.userStateUrl;
        request.body = {
            username: this.username,
            conn_id: this.connectionId,
            update_state: stateObj
        };
        for (let callable of this.mutators.userState) {
            callable(request);
        }
        request.handleError = this._handleSetUserStateError.bind(this);
        request.handleResponse = this._handleSetUserState.bind(this);
        request.execute();
    }

    /**
     * Subscribes user to channels.
     * @param channels {string[]} List of channels sent via POST to `subscribeUrl`.
     */
    subscribe(channels) {
        let request = new ChannelStreamRequest();
        request.url = this.subscribeUrl;
        request.body = {
            channels: channels,
            conn_id: this.connectionId
        };
        for (let callable of this.mutators.subscribe) {
            callable(request);
        }
        request.handleError = this._handleSubscribeError.bind(this);
        request.handleResponse = this._handleSubscribe.bind(this);
        if (request.body.channels && request.body.channels.length) {
            request.execute('POST');
        }
    }

    /**
     * Unsubscribes user from channels.
     * @param channels {string[]} List of channels sent via POST to `unsubscribeUrl`.
     */
    unsubscribe(channels) {
        let request = new ChannelStreamRequest();
        request.url = this.unsubscribeUrl;
        request.body = {
            channels: channels,
            conn_id: this.connectionId
        };
        for (let callable of this.mutators.unsubscribe) {
            callable(request);
        }
        request.handleError = this._handleUnsubscribeError.bind(this);
        request.handleResponse = this._handleUnsubscribe.bind(this);
        request.execute('POST');
    }

    /**
     * calculates list of channels we should add user to based on difference
     * between channels property and passed channel list
     * @param channels {string[]} List of channels to subscribe
     */
    calculateSubscribe(channels) {
        let toSubscribe = [];
        for (let channel of channels) {
            if (this.channels.indexOf(channel) === -1) {
                toSubscribe.push(channel);
            }
        }
        return toSubscribe;
    }

    /**
     * calculates list of channels we should remove user from based difference
     * between channels property and passed channel list
     * @param channels {string[]} List of channels to un-subscribe
     */
    calculateUnsubscribe(channels) {
        if (!channels) {
            channels = []
        }
        let toUnsubscribe = [];

        for (let channel of channels) {
            if (this.channels.indexOf(channel) !== -1) {
                toUnsubscribe.push(channel);
            }
        }
        return toUnsubscribe;
    }

    /**
     * Marks the connection as expired via /disconnect API.
     *
     */
    disconnect() {
        let request = new ChannelStreamRequest();
        request.url = this.disconnectUrl + '?conn_id=' + this.connectionId;
        request.body = {
            conn_id: this.connectionId
        };
        for (let callable of this.mutators.disconnect) {
            callable(request);
        }
        request.handleResponse = this._handleDisconnect.bind(this);
        request.execute();
        this.closeConnection();
    }

    /**
     * Sends a POST to the web application backend.
     * @param message {object} Message object sent via POST to `messageUrl`.
     */
    message(message) {
        let request = new ChannelStreamRequest();
        request.url = this.messageUrl;
        request.body = message;
        for (let callable of this.mutators.message) {
            callable(request);
        }
        request.handleError = this._handleMessageError.bind(this);
        request.handleResponse = this._handleMessage.bind(this);
        request.execute('POST');
    }

    /**
     * Sends a DELETE request to the web application backend.
     * @param message {object} Message object sent to DELETE to `messageUrl`.
     */
    delete(message) {
        let request = new ChannelStreamRequest();
        request.url = this.messageDeleteUrl;
        for (let callable of this.mutators.messageDelete) {
            callable(request);
        }
        request.body = message;
        request.handleError = this._handleMessageDeleteError.bind(this);
        request.handleResponse = this._handleMessageDelete.bind(this);
        request.execute('DELETE');
    }

    /**
     * Sends a PATCH request to the web application backend.
     * @param message {object} Message object sent via PATCH to `messageUrl`.
     */
    edit(message) {
        let request = new ChannelStreamRequest();
        request.url = this.messageEditUrl;
        request.body = message;
        for (let callable of this.mutators.messageEdit) {
            callable(request);
        }
        request.handleError = this._handleMessageEditError.bind(this);
        request.handleResponse = this._handleMessageEdit.bind(this);
        request.execute('PATCH');
    }

    /**
     * Opens "long lived" (websocket/longpoll) connection to the channelstream server.
     * @param request
     * @param data
     */
    startListening(request, data) {
        this.beforeListeningCallback(request, data);
        if (this.noWebsocket === false) {
            this.noWebsocket = !window.WebSocket;
        }
        if (this.noWebsocket === false) {
            this.openWebsocket();
        }
        else {
            this.openLongPoll();
        }
    }

    /**
     * Fired before connection start listening for messages
     * @param request
     * @param data
     */
    beforeListeningCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('beforeListeningCallback', request, data);
    }

    /**
     * Opens websocket connection.
     *
     */
    openWebsocket() {
        let url = this.websocketUrl + '?conn_id=' + this.connectionId;
        this.websocket = new WebSocket(url);
        this.websocket.onopen = this._handleListenOpen.bind(this);
        this.websocket.onclose = this._handleWebsocketCloseEvent.bind(this);
        this.websocket.onerror = this._handleListenErrorEvent.bind(this);
        this.websocket.onmessage = this._handleListenWSMessageEvent.bind(this);
    }

    /**
     * Opens long-poll connection.
     *
     */
    openLongPoll() {
        let request = new ChannelStreamRequest();
        request.url = this.longPollUrl + '?conn_id=' + this.connectionId;
        request.handleError = this._handleListenErrorEvent.bind(this);
        request.handleRequest = function () {
            this.connected = true;
            this.listenOpenedCallback(request);
        }.bind(this);
        request.handleResponse = function (request, data) {
            this._handleListenMessageEvent(data);
        }.bind(this);
        request.execute();
        this._ajaxListen = request;
    }

    /**
     * Retries `connect()` call while incrementing interval between tries up to 1 minute.
     *
     */
    retryConnection() {
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
    }

    /**
     * Closes currently listening connection.
     *
     */
    closeConnection() {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.onclose = null;
            this.websocket.onerror = null;
            this.websocket.close();
        }
        if (this._ajaxListen) {
            let request = this._ajaxListen.request;
            request.abort();
        }
        this.connected = false;
        this.connectionClosedCallback();
    }

    /**
     * Fired when listening connection is closed
     */
    connectionClosedCallback() {
        if (!this.debug) {
            return;
        }
        console.log('connectionClosedCallback');
    }

    /**
     * Fired when channels property get mutated
     */
    channelsChangedCallback(data) {
        if (!this.debug) {
            return;
        }
        console.log('channelsChangedCallback', data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleListenOpen(request, data) {
        this.connected = true;
        this.listenOpenedCallback(request, data);
        this.createHeartBeats();
    }

    /**
     * Fired when client starts listening for messages
     * @param request
     * @param data
     */
    listenOpenedCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('listenOpenedCallback', request, data);
    }

    /**
     * Starts sending heartbeats to maintain connection and notify server
     */
    createHeartBeats() {
        if (typeof this._heartbeat === 'undefined' && this.websocket !== null && this.heartbeats) {
            this._heartbeat = setInterval(this._sendHeartBeat.bind(this), 10000);
        }
    }

    _sendHeartBeat() {
        if (this.websocket.readyState === WebSocket.OPEN && this.heartbeats) {
            this.websocket.send(JSON.stringify({type: 'heartbeat'}));
        }
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleListenError(request, data) {
        this.connected = false;
        this.retryConnection(request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleConnectError(request, data) {
        this.connected = false;
        this.retryConnection(request, data);
        this.connectErrorCallback(request, data);
    }

    /**
     * Fired when client fails connect() call
     * @param request
     * @param data
     */
    connectErrorCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('connectErrorCallback', request, data);
    }

    /**
     * Handles long-polling payloads
     * @param data
     * @private
     */
    _handleListenMessageEvent(data) {
        setTimeout(this.openLongPoll.bind(this), 0);
        this.listenMessageCallback(data);
    }

    /**
     * Handles ws payloads
     * @param data
     * @private
     */
    _handleListenWSMessageEvent(data) {
        let parsedData = JSON.parse(data.data);
        this.listenMessageCallback(parsedData);
    }

    /**
     * Fired when messages are received
     * @param data
     */
    listenMessageCallback(data) {
        if (!this.debug) {
            return;
        }
        console.log('listenMessageCallback', data)
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleWebsocketCloseEvent(request, data) {
        this.connected = false;
        this.listenCloseCallback(request, data);
        this.retryConnection();
    }

    /**
     * Fired on websocket connection close event
     * @param request
     * @param data
     */
    listenCloseCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('listenCloseCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleListenErrorEvent(request, data) {
        this.connected = false;
        this.listenErrorCallback(request, data);
    }

    /**
     * Fired on long-pool/websocket connection error event
     * @param request
     * @param data
     */
    listenErrorCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('listenErrorCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleConnect(request, data) {
        this.currentBounceIv = 0;
        this.connectionId = data.conn_id;
        this.channels = data.channels;
        this.channelsChangedCallback(this.channels);
        this.connectCallback(request, data);
        this.startListening(request, data);
    }

    /**
     * Fired on successful connect() call
     * @param request
     * @param data
     */
    connectCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('connectCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleDisconnect(request, data) {
        this.connected = false;
        this.disconnectCallback(request, data);
    }

    /**
     * Fired after successful disconnect() call
     * @param request
     * @param data
     */
    disconnectCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('disconnectCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleMessage(request, data) {
        this.messageCallback(request, data);
    }

    /**
     * Fired on successful message() call
     * @param request
     * @param data
     */
    messageCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('messageCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleMessageError(request, data) {
        this.messageErrorCallback(request, data);
    }

    /**
     * Fired on message() call error
     * @param request
     * @param data
     */
    messageErrorCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('messageErrorCallback', request, data)
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleMessageEdit(request, data) {
        this.messageEditCallback(request, data);
    }

    /**
     * Fired on successful edit() call
     * @param request
     * @param data
     */
    messageEditCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('messageCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleMessageEditError(request, data) {
        this.messageEditErrorCallback(request, data);
    }

    /**
     * Fired on edit() call error
     * @param request
     * @param data
     */
    messageEditErrorCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('messageEditErrorCallback', request, data)
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleMessageDelete(request, data) {
        this.messageDeleteCallback(request, data);
    }

    /**
     * Fired on successful delete() call
     * @param request
     * @param data
     */
    messageDeleteCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('messageCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleMessageDeleteError(request, data) {
        this.messageDeleteErrorCallback(request, data);
    }

    /**
     * Fired on delete() call error
     * @param request
     * @param data
     */
    messageDeleteErrorCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('messageDeleteErrorCallback', request, data)
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleSubscribe(request, data) {
        this.channels = data.channels;
        this.channelsChangedCallback(this.channels);
        this.subscribeCallback(request, data);
    }

    /**
     * Fired on successful subscribe() call
     * @param request
     * @param data
     */
    subscribeCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('subscribeCallback', request, data)
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleSubscribeError(request, data) {
        this.subscribeErrorCallback(request, data);
    }

    /**
     * Fired on subscribe() call error
     * @param request
     * @param data
     */
    subscribeErrorCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('subscribeErrorCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleUnsubscribe(request, data) {
        this.channels = data.channels;
        this.channelsChangedCallback(this.channels);
        this.unsubscribeCallback(request, data);
    }

    /**
     * Fired on successful unsubscribe() call
     * @param request
     * @param data
     */
    unsubscribeCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('unsubscribeCallback', request, data);
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleUnsubscribeError(request, data) {
        this.unsubscribeErrorCallback(request, data);
    }

    /**
     * Fired on unsubscribe() call error
     * @param request
     * @param data
     */
    unsubscribeErrorCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('unsubscribeErrorCallback', request, data)
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleSetUserState(request, data) {
        this.setUserStateCallback(request, data);
    }

    /**
     * Fired on successful updateUserState() call
     * @param request
     * @param data
     */
    setUserStateCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('setUserStateCallback', request, data)
    }

    /**
     *
     * @param request
     * @param data
     * @private
     */
    _handleSetUserStateError(request, data) {
        this.setUserStateErrorCallback(request, data);
    }

    /**
     * Fired on updateUserState() error
     * @param request
     * @param data
     */
    setUserStateErrorCallback(request, data) {
        if (!this.debug) {
            return;
        }
        console.log('setUserStateErrorCallback', request, data);
    }
};

/**
 * Base class for making ajax requests
 */
class ChannelStreamRequest {

    constructor() {
        this.headers = [];
        this.body = null;
        this.url = '';
        this.request = null;
    }

    /**
     * Placeholder for error handling function
     * @param request
     * @param respText
     */
    handleError(request, respText) {
        console.error('request', request);
        console.error('respText', respText);
    };

    /**
     * Placeholder for sucessful response handler
     * @param request
     * @param respText
     */
    handleResponse(request, respText) {
        console.info('request', request);
        console.info('respText', respText);
    };

    /**
     * Placeholder for in-progress requests
     * @param request
     */
    handleRequest(request) {
    };

    handleStateChange() {
        let result = this.request.responseText;
        try {
            result = JSON.parse(result);
        } catch (exc) {

        }
        if (this.request.readyState === XMLHttpRequest.DONE) {
            if (this.request.status && this.request.status <= 400) {
                this.handleResponse(this.request, result);
            } else {
                this.handleError(this.request, result);
            }
        }
        else {
            this.handleRequest(this.request);
        }
    };

    /**
     * Execute AJAX request using specific verb, can send JSON payloads
     * @param verb {string} HTTP verb
     */
    execute(verb) {
        this.request = new XMLHttpRequest();
        this.request.onreadystatechange = this.handleStateChange.bind(this);
        if (this.headers) {
            for (let i = 0; i < this.headers.length; i++) {
                this.request.setRequestHeader(
                    this.headers[i].name, this.headers[i].value);
            }
        }
        if (this.body) {
            this.request.open(verb || 'POST', this.url);
            this.request.setRequestHeader('Content-Type', 'application/json');
            this.request.send(JSON.stringify(this.body));
        }
        else {
            this.request.open(verb || 'GET', this.url);
            this.request.send();
        }
    };
}
