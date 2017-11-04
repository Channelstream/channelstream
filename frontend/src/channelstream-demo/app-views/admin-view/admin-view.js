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
        var keys = Object.keys(event.detail.response.channels);
        var channels = [];
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            channels.push(event.detail.response.channels[key])
        }
        this.channels = channels;
    }

    toggleHistory(event) {
        var index = event.currentTarget.get('index');
        if (index !== undefined) {
            this.shadowRoot.querySelector('.channel-history-' + index).toggle();
        }
    }

    toggleUsers(event) {
        var index = event.currentTarget.get('index');
        if (index !== undefined) {
            this.shadowRoot.querySelector('.channel-users-' + index).toggle();
        }
    }
}

customElements.define(AdminView.is, AdminView);
