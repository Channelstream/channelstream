Polymer({
    is: 'chat-view',
    // this is required so we can pass visible/hidden state to message list and iron-list
    behaviors: [
        Polymer.IronResizableBehavior
    ],
    properties: {
        channels: Array,
        selectedChannel: {
            type: String,
            value: 'pub_chan',
            notify: true
        },
        user: {
            type: Object,
            notify: true
        },
        userState: {
            type: Object,
            value: function () {
                return {}
            },
            notify: true
        },
        usersStates: {
            type: Object,
            value: function () {
                return {}
            },
            notify: true
        },
        channelsStates: {
            type: Object,
            value: function () {
                return {}
            },
            notify: true
        },
        messages: {
            type: Object,
            value: function () {
                return {}
            },
            notify: true
        },
        visibleChannelMessages: {
            type: Array,
            computed: '_computeVisibleMessages(messages.*, selectedChannel)',
            notify: true
        },
        visibleChannelUsers: {
            type: Array,
            computed: '_computeVisibleUsers(channelsStates.*, selectedChannel)',
            notify: true
        }
    },
    attached: function () {
        this.async(this.notifyResize, 1);
    },

    /** Act only on various message types */
    addMessage: function (message) {
        // create a new key for channel
        if (typeof this.messages[message.channel] === 'undefined') {
            this.messages[message.channel] = [];
        }

        // push message
        if (message.type === 'message') {
            this.push(['messages', message.channel], message);
        }
        else if (message.type === 'presence') {
            var text = 'User ' + message.user + ' ' + message.message.action;
            // set presence text and normalize to format message element expects
            message.message = {
                text: text,
                email: '',
                action: message.message.action
            };
            this.push(['messages', message.channel], message);
        }
    },
    loadHistory: function (messageList, channel) {
        this.set(['messages', channel], messageList);
    },

    isAnonymous: function (username) {
        return username.toLowerCase().indexOf('anonymous') !== -1;
    },
    openDialog: function () {
        this.$.loginDialog.open();
    },
    changeUser: function (event) {
        event.preventDefault();
        if (this.$['login-form'].validate()) {
            this.set('user', {
                    username: this.loginUsername,
                    email: this.loginEmail
                }
            );
            this.$.loginDialog.close();
        }
    },
    /** stop default form submit because shady dom might fire it twice */
    formPresubmit: function (event) {
        event.preventDefault();
    },
    /** sends the signal that will pass the message to the
     * channelstream-connection element */
    sendMessage: function (event) {
        event.preventDefault();
        this.fire('iron-signal', {
            name: 'send-message',
            data: {
                message: {
                    text: this.message,
                    email: this.user.email,
                },
                channel: this.selectedChannel,
                user: this.user.username,
            }
        });
        this.$$('#message-form paper-input').value = '';
    },

    _computeVisibleMessages: function () {
        this.linkPaths(
            'visibleChannelMessages',
            'messages.' + this.selectedChannel);
        if (this.messages && this.selectedChannel) {
            return this.messages[this.selectedChannel];
        }
        return []
    },
    _computeVisibleUsers: function () {
        this.linkPaths(
            'visibleChannelUsers',
            'channelsStates.' + this.selectedChannel + '.users');
        if (this.channelsStates[this.selectedChannel]) {
            return this.channelsStates[this.selectedChannel].users;
        }
        return [];

    }
});
