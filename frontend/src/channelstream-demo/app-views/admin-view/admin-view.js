Polymer({
    is: 'admin-view',
    properties: {
        channels: {
            type: Array,
            value: []
        },
        loadingAdmin: {
            type: Boolean,
            observer: 'loadingChange'
        },
        ironSelected: {
            type: Boolean,
            observer: 'ironChange'
        },
        user: Object
    },

    ready: function () {
        // refresh data when document is attached to dom
        this.refresh();
    },

    refresh: function () {
        this.$['ajax-admin-info'].url = AppConf.infoUrl;
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

    ironChange: function (newVal, oldVal) {
        // refresh the data every 5s
        if (newVal) {
            this._addInterval();
        }
        else {
            this._clearInterval();
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
