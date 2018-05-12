import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import '@polymer/iron-ajax/iron-ajax.js';
import '@polymer/paper-progress/paper-progress.js';
import './server-info.js';
import '../debug.js';
import { connect } from 'pwa-helpers/connect-mixin.js';
import {store} from './redux/store.js';
import {actions as channelsActions} from './redux/server_info/channels';
import {actions as statsActions} from './redux/server_info/server_stats';
import {actions as currentActions} from './redux/current_actions';

class ChannelStreamAdmin extends connect(store)(PolymerElement) {

    static get template() {
        return html`
        <style>
            .transparent {
                opacity: 0;
            }

            #admin-page-progress {
                width: 100%;
                --paper-progress-indeterminate-cycle-duration: 3s;
                margin-bottom: 15px;
                transition-duration: 500ms;
            }
        </style>

        <iron-ajax
            id="ajax-admin-info"
            url=""
            handle-as="json"
            loading="{{loadingInfo}}"
            data-type="SERVER_INFO"
            on-request="_handleAjaxRequest"
            on-error="_handleAjaxRequestError"
            on-response="_handleAjaxResponse">
        </iron-ajax>

        <paper-progress id="admin-page-progress" indeterminate class="transparent" transparent="[[loadingAdmin]]"></paper-progress>

        <server-info channels="[[channels]]" server-stats="[[serverStats]]"></server-info>
        `;
    }

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
                type: Array
            },
            serverStats: {
                type: Object
            },
            currentActions: {
                type: Array
            },
            loadingInfo: {
                type: Boolean,
                observer: 'loadingChange'
            }
        };
    }

    _stateChanged(state) {
        this.channels = state.serverInfo.channels;
        this.serverStats = state.serverInfo.serverStats;
        this.currentActions = state.serverInfo.currentActions;
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
        store.dispatch(currentActions.currentActionStart(
            event.target.dataset.type, event.detail));
    }

    _handleAjaxRequestError(event){
        store.dispatch(currentActions.currentActionError(
            event.target.dataset.type, event.detail.error.message));
    }

    _handleAjaxResponse(event) {
        let response = event.detail.response;
        store.dispatch(currentActions.currentActionFinish(
            event.target.dataset.type, response));
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
    }

}

customElements.define(ChannelStreamAdmin.is, ChannelStreamAdmin);
