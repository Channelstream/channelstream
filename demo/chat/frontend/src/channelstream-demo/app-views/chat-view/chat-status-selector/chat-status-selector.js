import {LitElement, html} from 'lit-element';
import 'weightless/select/select.js';


class ChatStatusSelector extends LitElement {

    render() {
        return html`
       <wl-select name="value" label="Status Color?" @input=${(e) => this._changeColor(e)}>
          <option value="black">Black</option>
          <option value="red">Red</option>
          <option value="green">Green</option>
          <option value="blue">Blue</option>
       </wl-select>
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
        console.log(event.target);
        this.dispatchEvent(new CustomEvent('change-status', {
            detail: {color: event.target.value},
            bubbles: true,
            composed: true
        }));
    }
}

customElements.define(ChatStatusSelector.is, ChatStatusSelector);
