import {LitElement, html} from '@polymer/lit-element';


class AppDebug extends LitElement {

    _render({data}) {
        return html`
        <style>
            pre{
                padding: 5px;
                border: 1px solid;
            }
        </style>
        <pre>${JSON.stringify(data, null, 4)}</pre>
        `
    }

    static get is() {
        return 'app-debug';
    }

    static get properties() {
        return {
            data: {
                type: Object
            }
        };
    }
}

customElements.define(AppDebug.is, AppDebug);

