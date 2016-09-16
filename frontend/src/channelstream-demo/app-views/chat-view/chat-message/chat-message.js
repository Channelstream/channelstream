Polymer({
    is: 'chat-message',
    properties: {
        user: String,
        timestamp: Object,
        message: Object,
        channel: String,
        type: String
    },
    _shortTime: function () {
        return this.timestamp.split('.')[0]
    }
});
