Polymer({
    is: 'chat-status-selector',
    properties: {
        isReady: Boolean,
        selected: {
            type: String,
            value: "black",
            observer: '_changeColor'
        }
    },

    ready: function () {
        this.isReady = true
    },

    _changeColor: function () {
        if (!this.isReady) {
            return
        }
        this.fire('iron-signal', {
            name: 'change-status',
            data: {color: this.selected}
        });
    }
});
