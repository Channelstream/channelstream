import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';
// import 'web-animations-js/web-animations.min.js';
import '@polymer/paper-listbox/paper-listbox.js';
import '@polymer/paper-dropdown-menu/paper-dropdown-menu.js';
import '@polymer/paper-item/paper-item.js';


class ChatStatusSelector extends PolymerElement {

    static get template(){
        return html`
        <style>
            paper-item {
                width: 150px;
            }
        </style>
        <paper-dropdown-menu label="Status Color">
            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="{{selected}}" attr-for-selected="value">
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
            selected: {
                type: String,
                value: "black",
                observer: '_changeColor'
            }
        };
    }

    _changeColor() {
        this.dispatchEvent(new CustomEvent('change-status', {
            detail: {color: this.selected},
            bubbles: true,
            composed: true
        }));

    }
}

customElements.define(ChatStatusSelector.is, ChatStatusSelector);
