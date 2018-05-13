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


const fetchServerInfo = (url, store) => {
    const action_type = 'SERVER_INFO';
    store.dispatch(currentActions.currentActionStart(
        action_type, {url}));

    fetch(url, {
        method: 'get',
        credentials: 'same-origin'
    }).then(function(response) {
        return response.json();
    }).then(function(response) {
        // let response = event.detail.response;
        console.log('x',response)
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
                type: Object,
                observer: 'loadingChange'
            }
        };
    }

    _stateChanged(state) {
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
        fetchServerInfo(this.appConfig.urls.jsonUrl, store);
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
        if (this.currentActions.active.length) {
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

}

customElements.define(ChannelStreamAdmin.is, ChannelStreamAdmin);

export {fetchServerInfo};