import {LitElement, html} from 'lit-element';
import {repeat} from 'lit-html/directives/repeat.js';
import '@material/mwc-icon/mwc-icon.js';
import '@material/mwc-button/mwc-button.js';
import '../debug.js';
import '../universal-collapse.js';

class ServerInfo extends LitElement {

    render() {

        let channels = this.channels;
        let serverStats = this.serverStats;
        let selectedChannel = this.selectedChannel;
        let channelInfo = html`No channel selected`;

        if (selectedChannel) {
            let channel = channels.filter((i) => i.uuid === selectedChannel)[0];

            channelInfo = html`
            <div class="channel-${channel.uuid} paper-card">
                <h1>Channel: ${channel.name}</h1>
                <div class="card-actions">
                    <span>
                    <mwc-button raised toggles @click=${(e) => this.toggleHistory(channel.uuid)} title="Shows this channels history">
                         <mwc-icon>history</mwc-icon>History</mwc-button>
                    </span>
                    <span>
                    <mwc-button raised toggles @click=${(e) => this.toggleUsers(channel.uuid)} title="Shows currently connected users">
                        <mwc-icon>account_box</mwc-icon>Users</mwc-button>
                    </span>
                </div>
                <div class="card-content">
                    <ul>
                        <li><strong>Long name</strong>: ${channel.long_name}</li>
                        <li><strong>last active</strong>: ${channel.last_active}</li>
                        <li><strong>Total connections</strong>: ${channel.total_connections}</li>
                        <li><strong>Total users</strong>: ${channel.total_users}</li>
                    </ul>
                    <p><strong>Config</strong></p>
                    <app-debug .data="${channel.settings}"></app-debug>

                    <universal-collapse class="channel-history-${channel.uuid}" collapsed>
                        <div class="history-holder">
                            <strong>Message history:</strong>
                            ${channel.history.map((item) => html`
                            <app-debug .data="${item}"></app-debug>
                            `)}
                        </div>
                    </universal-collapse>

                    <universal-collapse class="channel-users-${channel.uuid}" collapsed>
                        <div class="users-holder">
                            <strong>Connected users:</strong>
                            ${channel.users.map((item) => html`
                            <div>${item}</div>
                            `)}
                        </div>
                    </universal-collapse>

                </div>
            </div>
            `
        }

        return html`
        <style>
            .server-stat {
                padding: 0 15px 0 0;
                margin: 0 25px 25px 0;
                display: inline-block;
                position: relative;
            }

            .paper-card {
                padding: 25px;
            }

            mwc-button mwc-icon {
                margin-right: 10px;
            }

            h1{
                margin-top: 0;
            }

            .card-actions{
                margin: 15px 0px;
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

            .badge{
                font-weight: bold;
                border: 1px solid #eeeeee;
                display: inline-block;
                border-radius: 15px;
                padding: 10px 15px;
            }
            .flex-parent{
                 display: flex;
            }
            .column-left{
                width: 300px;
            }
            .column-right{
                flex-grow: 1;
            }
        </style>

        <div class="server-stat">
            Uptime ${serverStats.uptime}
        </div>
        <div class="server-stat">
            Unique users remembered
            <div class="badge">${serverStats.remembered_user_count}</div>
        </div>
        <div class="server-stat">
            Unique users connected
            <div class="badge">${serverStats.unique_user_count}</div>
        </div>
        <div class="server-stat">
            Total connections
            <div class="badge">${serverStats.total_connections}</div>
        </div>

        <div class="server-stat">
            Total channels
            <div class="badge">${serverStats.total_channels}</div>
        </div>

        <div class="server-stat">
            Messages since start
            <div class="badge">${serverStats.total_unique_messages}</div>
        </div>

        <div class="server-stat">
            All frames sent
            <div class="badge">${serverStats.total_messages}</div>
        </div>

        <div class="flex-parent">
            <div class="column-left">
            <ul>
            ${repeat(channels, (channel) => channel.name, (channel, index) => html`
            <li><mwc-button @click="${(e) => this.selectChannel(channel.uuid)}">${index + 1} - ${channel.name}</mwc-button></li>
            `)}
            </ul>
            </div>
            <div class="column-right">
                ${channelInfo}
            </div>
        </div>
        `;
    }

    static get is() {
        return 'server-info';
    }

    static get properties() {
        return {
            channels: Array,
            serverStats: Object,
            selectedChannel: String
        };
    }

    selectChannel(channelId) {
        this.selectedChannel = channelId;
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
