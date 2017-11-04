class ChannelStreamAdmin extends Polymer.Element {

    static get is() {
        return 'channelstream-admin';
    }

    static get properties() {
        return {
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
        };
    }

    ready() {
        super.ready();
        // refresh data when document is attached to dom
        this.$['ajax-admin-info'].url = this.urlAdminJson;
        this.refresh();
        this._addInterval();
    }

    refresh() {
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

customElements.define(ChannelStreamAdmin.is, ChannelStreamAdmin);
