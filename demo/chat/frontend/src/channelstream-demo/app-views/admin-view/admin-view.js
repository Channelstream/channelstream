import {LitElement, html} from '@polymer/lit-element';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../redux/store.js';

import '@polymer/iron-ajax/iron-ajax.js';
import '@polymer/paper-progress/paper-progress.js';
import '../../../../../../../frontend/src/channelstream-admin/server-info.js';
import {fetchServerInfo} from '../../../../../../../frontend/src/channelstream-admin/channelstream-admin';

class AdminView extends connect(store)(LitElement) {

    render() {
        return html`
        <style>
            #admin-page-progress {
                width: 100%;
                --paper-progress-indeterminate-cycle-duration: 3s;
                margin-bottom: 15px;
            }
        </style>

        <paper-progress id="admin-page-progress" indeterminate ?disabled=${this.currentActions.active.length === 0}></paper-progress>

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

    _stateChanged(state) {
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

    loadingChange(newVal) {
        if (newVal) {
            this.shadowRoot.querySelector('paper-progress').toggleClass('transparent', false);
        }
        else {
            this.shadowRoot.querySelector('paper-progress').toggleClass('transparent', true);
        }
    }


}

customElements.define(AdminView.is, AdminView);
