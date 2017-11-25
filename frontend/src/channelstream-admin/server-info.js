import {ReduxMixin} from './redux/store';
import {actions as channelsActions} from './redux/server_info/channels';
import {actions as statsActions} from './redux/server_info/server_stats';
import {actions as currentActions} from './redux/current_actions';

class ServerInfo extends Polymer.Element {

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

customElements.define(ServerInfo.is, ServerInfo);
