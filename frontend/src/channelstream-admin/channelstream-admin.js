Polymer({
    is: 'channelstream-admin',
    properties: {
        urlAdminJson: String,
        channels: {
            type: Array,
            value: []
        },
        loadingAdmin: {
            type: Boolean,
            observer: 'loadingChange'
        },
        user: Object
    },

    ready: function () {
        // refresh data when document is attached to dom
        this.$['ajax-admin-info'].url = this.urlAdminJson;
        this.refresh();
        this._addInterval();
    },

    refresh: function () {
        this.$['ajax-admin-info'].generateRequest();
    },

    _addInterval: function () {
        this.interval = setInterval(this.refresh.bind(this), 5000)
    },

    _clearInterval: function () {
        if (this.interval) {
            clearInterval(this.interval);
        }
    },
    loadingChange: function (newVal) {
        if (newVal) {
            this.$$('paper-progress').toggleClass('transparent', false);
        }
        else {
            this.$$('paper-progress').toggleClass('transparent', true);
        }
    },
    setChannels: function (event) {
        // changes channels object response to a list for iteration in template
        var keys = Object.keys(event.detail.response.channels);
        var channels = [];
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            channels.push(event.detail.response.channels[key])
        }
        this.channels = channels;
    },

    toggleHistory: function (event) {
        var index = event.currentTarget.get('index');
        if(index !== undefined){
            this.$$('.channel-history-' + index).toggle();
        }
    },

    toggleUsers: function (event) {
        var index = event.currentTarget.get('index');
        if(index !== undefined){
            this.$$('.channel-users-' + index).toggle();
        }
    }

});