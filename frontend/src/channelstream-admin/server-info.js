import {LitElement, html} from '@polymer/lit-element';
import { repeat } from 'lit-html/lib/repeat.js';
import '@polymer/iron-collapse/iron-collapse.js';
import '@polymer/iron-icons/iron-icons.js';
import '@polymer/iron-icons/social-icons.js';
import '@polymer/paper-badge/paper-badge.js';
import '@polymer/paper-button/paper-button.js';
import '@polymer/paper-card/paper-card.js';
import '@polymer/paper-tooltip/paper-tooltip.js';
import '../debug.js';

import {ReduxMixin} from './redux/store';
import {actions as channelsActions} from './redux/server_info/channels';
import {actions as statsActions} from './redux/server_info/server_stats';
import {actions as currentActions} from './redux/current_actions';

class ServerInfo extends LitElement {

    _render({channels, serverStats}) {
        return html`
        <style>
            .server-stat {
                padding: 0 15px 0 0;
                margin: 0 25px 25px 0;
                display: inline-block;
                position: relative;
            }

            .server-stat > paper-badge {
                --paper-badge-margin-bottom: -20px;
            }

            paper-card {
                width: 100%;

            }

            paper-material {
                padding: 25px;
            }

            paper-button iron-icon {
                margin-right: 10px;
            }

            ul {
                margin: 0;
                padding: 0;
                list-style: none;
            }

            .users-holder {
                padding-top: 20px
            }

            .history-holder {
                padding-top: 20px
            }

        </style>

        <div class="server-stat">
            Uptime ${serverStats.uptime}
        </div>
        <div class="server-stat">
            Unique users remembered
            <paper-badge label="${serverStats.remembered_user_count}"></paper-badge>
        </div>
        <div class="server-stat">
            Unique users connected
            <paper-badge label="${serverStats.unique_user_count}"></paper-badge>
        </div>
        <div class="server-stat">
            Total connections
            <paper-badge label="${serverStats.total_connections}"></paper-badge>
        </div>

        <div class="server-stat">
            Total channels
            <paper-badge label="${serverStats.total_channels}"></paper-badge>
        </div>

        <div class="server-stat">
            Messages since start
            <paper-badge label="${serverStats.total_unique_messages}"></paper-badge>
        </div>

        <div class="server-stat">
            All frames sent
            <paper-badge label="${serverStats.total_messages}"></paper-badge>
        </div>

            ${repeat(channels, (channel) => channel.name, (channel, index) => html`
            <paper-card heading="channel: ${channel.name}" class$="channel-${channel.id}">
                <div class="card-content">
                ${index}
                    <ul>
                        <li><strong>Long name</strong>: ${channel.long_name}</li>
                        <li><strong>last active</strong>: ${channel.last_active}</li>
                        <li><strong>Total connections</strong>: ${channel.total_connections}</li>
                        <li><strong>Total users</strong>: ${channel.total_users}</li>
                    </ul>
                    <p><strong>Config</strong></p>
                    <app-debug data="${channel.settings}"></app-debug>

                    <iron-collapse class$="channel-history-${channel.id}">
                        <div class="history-holder">
                            <strong>Message history:</strong>
                            ${channel.history.map((item) => html`
                            <app-debug data="${item}"></app-debug>
                            `)}
                        </div>
                    </iron-collapse>

                    <iron-collapse class$="channel-users-${channel.id}">
                        <div class="users-holder">
                            <strong>Connected users:</strong>
                            ${channel.users.map((item) => html`
                            <div>${item}</div>
                            `)}
                        </div>
                    </iron-collapse>

            </div>
            <div class="card-actions">
                <span>
                <paper-button raised toggles on-tap=${(e) => this.toggleHistory(channel.id)}">
                    <iron-icon icon="icons:history"></iron-icon>History</paper-button>
                <paper-tooltip position="top" animation-delay="0">Shows this channels history</paper-tooltip>
                </span>
                <span>
                <paper-button raised toggles on-tap=${(e) => this.toggleUsers(channel.id)}">
                    <iron-icon icon="social:people-outline"></iron-icon>Users</paper-button>
                <paper-tooltip position="top" animation-delay="0">Shows currently connected users</paper-tooltip>
                </span>
            </div>
            </paper-card>
            `)}

        `;
    }

    static get is() {
        return 'server-info';
    }

    static get properties() {
        return {
            channels: {
                type: Array
            },
            serverStats: {
                type: Object
            }
        };
    }

    toggleHistory(index) {
        if (index !== undefined) {
            this.shadowRoot.querySelector('.channel-history-' + index).toggle();
        }
    }

    toggleUsers(index) {
        if (index !== undefined) {
            this.shadowRoot.querySelector('.channel-users-' + index).toggle();
        }
    }
}

customElements.define(ServerInfo.is, ServerInfo);
