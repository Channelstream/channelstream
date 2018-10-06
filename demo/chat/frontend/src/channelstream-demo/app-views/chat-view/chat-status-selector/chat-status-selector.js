import {LitElement, html} from '@polymer/lit-element';
import '@polymer/paper-listbox/paper-listbox.js';
import '@polymer/paper-dropdown-menu/paper-dropdown-menu.js';
import '@polymer/paper-item/paper-item.js';


class ChatStatusSelector extends LitElement {

    render() {
        return html`
        <style>
            paper-item {
                width: 150px;
            }
        </style>
        <paper-dropdown-menu label="Status Color">
            <paper-listbox slot="dropdown-content" class="dropdown-content" 
            @selected-changed=${(e) => this._changeColor(e)} attr-for-selected="value">
                <paper-item value="black">Black</paper-item>
                <paper-item value="red">Red</paper-item>
                <paper-item value="green">Green</paper-item>
                <paper-item value="blue">Blue</paper-item>
            </paper-listbox>
        </paper-dropdown-menu>
        `
    }

    static get is() {
        return 'chat-status-selector';
    }

    static get properties() {
        return {
            isReady: Boolean,
            selected: String
        };
    }

    constructor() {
        super();
        this.type = 'black';
    }

    _changeColor(event) {
        this.dispatchEvent(new CustomEvent('change-status', {
            detail: {color: event.target.selected},
            bubbles: true,
            composed: true
        }));
    }
}

customElements.define(ChatStatusSelector.is, ChatStatusSelector);
