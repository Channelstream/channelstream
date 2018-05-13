import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
import {connect} from 'pwa-helpers/connect-mixin.js';
import {store} from '../../redux/store.js';

import '@polymer/iron-ajax/iron-ajax.js';
import '@polymer/paper-progress/paper-progress.js';
import '../../../channelstream-admin/server-info.js';
import {fetchServerInfo} from '../../../channelstream-admin/channelstream-admin';
import {actions as currentActions} from "../../../channelstream-admin/redux/current_actions";
import {actions as statsActions} from "../../../channelstream-admin/redux/server_info/server_stats";
import {actions as channelsActions} from "../../../channelstream-admin/redux/server_info/channels";

class AdminView extends connect(store)(PolymerElement) {

    static get template(){
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

        <paper-progress id="admin-page-progress" indeterminate class="transparent"></paper-progress>

        <server-info channels="[[channels]]" server-stats="[[serverStats]]"></server-info>
        `
    }
    
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
                type: Array
            },
            serverStats: {
                type: Object
            },
            currentActions: {
                type: Array
            },
            ironSelected: {
                type: Boolean,
                observer: 'ironChange'
            },
        };
    }

    _stateChanged(state) {
        this.user = state.user;
        this.channels = state.adminView.channels;
        this.serverStats = state.adminView.serverStats;
        this.currentActions = state.currentActions;
    }

    ready() {
        super.ready();
        // refresh data when document is attached to dom
        this.refresh();
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


}

customElements.define(AdminView.is, AdminView);
