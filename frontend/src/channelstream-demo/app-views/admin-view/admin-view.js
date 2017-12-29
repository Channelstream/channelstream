class AdminView extends Polymer.Element {

    static get is() {
        return 'admin-view';
    }

    static get properties() {
        return {
            channels: {
                type: Array,
                value: []
            },
            serverInfo: {
                type: Object
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
        };
    }

    ready() {
        super.ready()
        // refresh data when document is attached to dom
        this.refresh();
    }

    refresh() {
        this.$['ajax-admin-info'].url = AppConf.infoUrl;
        this.$['ajax-admin-info'].generateRequest();
    }

    _addInterval() {
        this.interval = setInterval(this.refresh.bind(this), 5000)
    }

    _clearInterval() {
        if (this.interval) {
            clearInterval(this.interval);
        }
    }

    ironChange(newVal, oldVal) {
        // refresh the data every 5s
        if (newVal) {
            this._addInterval();
        }
        else {
            this._clearInterval();
        }
    }

    loadingChange(newVal) {
        if (newVal) {
            this.shadowRoot.querySelector('paper-progress').toggleClass('transparent', false);
        }
        else {
            this.shadowRoot.querySelector('paper-progress').toggleClass('transparent', true);
        }
    }

    setChannels(event) {
        // changes channels object response to a list for iteration in template
        var response = event.detail.response;
        var keys = Object.keys(response.channels);
        var channels = [];
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            channels.push(response.channels[key]);
        }
        this.channels = channels;
        this.serverStats = {
            "remembered_user_count": response.remembered_user_count,
            "unique_user_count": response.unique_user_count,
            "total_connections": response.total_connections,
            "total_channels": response.total_channels,
            "total_messages": response.total_messages,
            "total_unique_messages": response.total_unique_messages,
            "uptime": response.uptime
        }
    }
}

customElements.define(AdminView.is, AdminView);
