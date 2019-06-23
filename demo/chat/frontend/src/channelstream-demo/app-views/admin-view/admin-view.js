import {LitElement, html} from 'lit-element';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../redux/store.js';

import '@material/mwc-linear-progress/mwc-linear-progress.js';
import '../../../../../../../frontend/src/channelstream-admin/server-info.js';
import {fetchServerInfo} from '../../../../../../../frontend/src/channelstream-admin/channelstream-admin';

class AdminView extends connect(store)(LitElement) {

    render() {
        return html`
        <style>
        </style>

        <mwc-linear-progress id="admin-page-progress" indeterminate .closed=${this.currentActions.active.length === 0}></mwc-linear-progress>

        <server-info .channels=${this.channels} .serverStats=${this.serverStats}></server-info>
        `;
    }

    static get is() {
        return 'admin-view';
    }

    static get properties() {
        return {
            channels: Array,
            serverStats: Object,
            currentActions: Array,
            ironSelected: Boolean
        };
    }

    constructor() {
        super();
        this.appConfig = window.AppConf;
    }

    stateChanged(state) {
        this.user = state.user;
        this.channels = state.adminView.channels;
        this.serverStats = state.adminView.serverStats;
        this.currentActions = state.currentActions;
    }

    connectedCallback() {
        super.connectedCallback();
        // refresh data when document is attached to dom
        this.refresh();
        this._addInterval();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        this._clearInterval();
    }

    refresh() {
        fetchServerInfo(this.appConfig.infoUrl, store);
    }

    _addInterval() {
        this.interval = setInterval(this.refresh.bind(this), 5000)
    }

    _clearInterval() {
        if (this.interval) {
            clearInterval(this.interval);
        }
    }
}

customElements.define(AdminView.is, AdminView);
