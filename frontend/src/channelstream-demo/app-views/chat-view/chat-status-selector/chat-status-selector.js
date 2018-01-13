class ChatStatusSelector extends Polymer.Element {

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
