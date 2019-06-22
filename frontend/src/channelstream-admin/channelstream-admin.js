import {LitElement, html} from 'lit-element';
import '@material/mwc-linear-progress/mwc-linear-progress.js';
import './server-info.js';
import '../debug.js';
import { connect } from 'pwa-helpers/connect-mixin.js';
import {store} from './redux/store.js';
import {actions as channelsActions} from './redux/server_info/channels';
import {actions as statsActions} from './redux/server_info/server_stats';
import {actions as currentActions} from './redux/current_actions';


const fetchServerInfo = (url, store) => {
    const action_type = 'SERVER_INFO';
    store.dispatch(currentActions.currentActionStart(
        action_type, {url}));

    fetch(url, {
        method: 'get',
        credentials: 'same-origin',
        cache: "no-store"
    }).then(function(response) {
        return response.json();
    }).then(function(response) {
        store.dispatch(currentActions.currentActionFinish(
            action_type, response));
        store.dispatch(statsActions.set({
            "remembered_user_count": response.remembered_user_count,
            "unique_user_count": response.unique_user_count,
            "total_connections": response.total_connections,
            "total_channels": response.total_channels,
            "total_messages": response.total_messages,
            "total_unique_messages": response.total_unique_messages,
            "uptime": response.uptime
        }));

        let channels = Object.values(response.channels);
        store.dispatch(channelsActions.set(channels));

    }).catch(function(err) {
        store.dispatch(currentActions.currentActionError(
            action_type, err));
    });

};

class ChannelStreamAdmin extends connect(store)(LitElement) {

    render() {
        return html`
        <mwc-linear-progress id="admin-page-progress" indeterminate .closed=${this.currentActions.active.length === 0}></mwc-linear-progress>
        <server-info .channels=${this.channels} .serverStats=${this.serverStats}></server-info>
        `;
    }

    static get is() {
        return 'channelstream-admin';
    }

    static get properties() {
        return {
            channels: Array,
            serverStats: Object,
            currentActions: Object
        };
    }

    constructor() {
        super();
        this.appConfig = window.AppConf;
    }

    stateChanged(state) {
        this.channels = state.serverInfo.channels;
        this.serverStats = state.serverInfo.serverStats;
        this.currentActions = state.currentActions;
    }

    connectedCallback() {
        super.connectedCallback();
        this.refresh();
        this._addInterval();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._clearInterval();
    }

    refresh() {
        fetchServerInfo(window.AppConf.urls.jsonUrl, store);
    }

    _addInterval() {
        this.interval = setInterval(this.refresh.bind(this), 5000);
    }

    _clearInterval() {
        if (this.interval) {
            clearInterval(this.interval);
        }
    }

    _handleAjaxRequest(event){
        store.dispatch(currentActions.currentActionStart(
            event.target.dataset.type, event.detail));
    }

    createRenderRoot() {
        /**
         * Render template in light DOM. Note that shadow DOM features like
         * encapsulated CSS are unavailable.
         */
        return this;
    }

}

customElements.define(ChannelStreamAdmin.is, ChannelStreamAdmin);

export {fetchServerInfo, ChannelStreamAdmin};
