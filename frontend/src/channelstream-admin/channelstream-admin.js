import {LitElement, html} from 'lit-element';
import '@material/mwc-linear-progress/mwc-linear-progress.js';
import './server-info.js';
import '../debug.js';
import { connect } from 'pwa-helpers/connect-mixin.js';
import {store} from './redux/store.js';


const fetchServerInfo = (url, store) => {
    const action_type = 'SERVER_INFO';
    store.dispatch({ type: 'currentActions/start', payload: {subtype:action_type, url} });

    fetch(url, {
        method: 'get',
        credentials: 'same-origin',
        cache: "no-store"
    }).then(function(response) {
        return response.json();
    }).then(function(response) {
        store.dispatch({ type: 'currentActions/finish', payload: {subtype:action_type, response} });
        store.dispatch({ type: 'serverStats/set', payload: {
                "remembered_user_count": response.remembered_user_count,
                "unique_user_count": response.unique_user_count,
                "total_connections": response.total_connections,
                "total_channels": response.total_channels,
                "total_messages": response.total_messages,
                "total_unique_messages": response.total_unique_messages,
                "uptime": response.uptime
            } });

        let channels = Object.values(response.channels);
        store.dispatch({ type: 'channelStats/set', payload: channels });

    }).catch(function(err) {
        store.dispatch({ type: 'currentActions/error', payload: {subtype: action_type, err} });
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
        this.channels = state.channelStats;
        this.serverStats = state.serverStats;
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
        this.interval = setInterval(this.refresh.bind(this), 10000);
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

export {ChannelStreamAdmin};
