import {LitElement, html} from 'lit-element';


class AppDebug extends LitElement {

    render() {
        return html`
        <style>
            pre{
                padding: 5px;
                border: 1px solid;
            }
        </style>
        <pre>${JSON.stringify(this.data, null, 4)}</pre>
        `
    }

    static get is() {
        return 'app-debug';
    }

    static get properties() {
        return {
            data: Object
        };
    }
}

customElements.define(AppDebug.is, AppDebug);
