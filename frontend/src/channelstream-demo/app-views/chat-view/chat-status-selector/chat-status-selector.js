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

    ready() {
        super.ready()
        this.isReady = true
    }

    _changeColor() {
        if (!this.isReady) {
            return;
        }
        this.dispatchEvent(new CustomEvent('iron-signal', {
            detail: {
                name: 'change-status',
                data: {color: this.selected}
            },
            bubbles: true,
            composed: true
        }));

    }
}

customElements.define(ChatStatusSelector.is, ChatStatusSelector);
