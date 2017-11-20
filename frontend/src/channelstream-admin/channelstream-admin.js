import {ReduxMixin} from './redux/store';
import {actions as channelsActions} from './redux/server_info/channels';
import {actions as statsActions} from './redux/server_info/server_stats';
import {actions as currentActions} from './redux/current_actions';

class ChannelStreamAdmin extends ReduxMixin(Polymer.Element) {

    static get is() {
        return 'channelstream-admin';
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
                statePath: 'serverInfo.channels'
            },
            serverStats: {
                type: Object,
                statePath: 'serverInfo.serverStats'
            },
            currentActions: {
                type: Array,
                statePath: 'currentActions'
            },
            loadingInfo: {
                type: Boolean,
                observer: 'loadingChange'
            }
        };
    }

    static get actions() {
        return {
            ...currentActions,
            setChannels: channelsActions.set,
            setInfo: statsActions.set
        };
    }

    connectedCallback() {
        super.connectedCallback();
        // refresh data when document is attached to dom
        this.$['ajax-admin-info'].url = this.appConfig.urls.jsonUrl;
        this.refresh();
        this._addInterval();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._clearInterval();
    }

    refresh() {
        this.$['ajax-admin-info'].generateRequest();
    }

    _addInterval() {
        this.interval = setInterval(this.refresh.bind(this), 5000);
    }

    _clearInterval() {
        if (this.interval) {
            clearInterval(this.interval);
        }
    }

    loadingChange() {
        if (this.loadingInfo) {
            this.shadowRoot.querySelector('paper-progress').toggleClass('transparent', false);
        }
        else {
            this.shadowRoot.querySelector('paper-progress').toggleClass('transparent', true);
        }
    }

    _handleAjaxRequest(event){
        this.dispatch('currentActionStart', event.target.dataset.type, event.detail);
    }

    _handleAjaxRequestError(event){
        this.dispatch('currentActionError', event.target.dataset.type, event.detail.error.message);
    }

    _handleAjaxResponse(event) {
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

    toggleHistory(event) {
        let index = event.currentTarget.dataset['index'];
        if (index !== undefined) {
            this.shadowRoot.querySelector('.channel-history-' + index).toggle();
        }
    }

    toggleUsers(event) {
        let index = event.currentTarget.dataset['index'];
        if (index !== undefined) {
            this.shadowRoot.querySelector('.channel-users-' + index).toggle();
        }
    }
}

customElements.define(ChannelStreamAdmin.is, ChannelStreamAdmin);
