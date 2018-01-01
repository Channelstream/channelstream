import {ReduxMixin} from '../../redux/store';
import {actions as currentActions} from "../../../channelstream-admin/redux/current_actions";
import {actions as statsActions} from "../../../channelstream-admin/redux/server_info/server_stats";
import {actions as channelsActions} from "../../../channelstream-admin/redux/server_info/channels";

class AdminView extends ReduxMixin(Polymer.Element) {

    static get is() {
        return 'admin-view';
    }

    static get properties() {
        return {
            appConfig: {
                type: Array,
                value: () => {
                    return window.AppConf;
                }
            },
            channels: {
                type: Array,
                statePath: 'adminView.channels'
            },
            serverStats: {
                type: Object,
                statePath: 'adminView.serverStats'
            },
            currentActions: {
                type: Array,
                statePath: 'currentActions'
            },
            loadingInfo: {
                type: Boolean,
                observer: 'adminView.loadingChange'
            },
            ironSelected: {
                type: Boolean,
                observer: 'ironChange'
            },
        };
    }

    static get actions() {
        return {
            ...currentActions,
            setChannels: channelsActions.set,
            setInfo: statsActions.set
        };
    }

    ready() {
        super.ready();
        // refresh data when document is attached to dom
        this.refresh();
    }

    refresh() {
        this.$['ajax-admin-info'].url = this.appConfig.infoUrl;
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
        let response = event.detail.response;
        this.dispatch('currentActionFinish', event.target.dataset.type, response);
        this.dispatch('setInfo', {
            "remembered_user_count": response.remembered_user_count,
            "unique_user_count": response.unique_user_count,
            "total_connections": response.total_connections,
            "total_channels": response.total_channels,
            "total_messages": response.total_messages,
            "total_unique_messages": response.total_unique_messages,
            "uptime": response.uptime
        });

        let channels = Object.values(response.channels);
        this.dispatch('setChannels', channels);
    }
}

customElements.define(AdminView.is, AdminView);
