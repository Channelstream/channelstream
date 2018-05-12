import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';


class AppDebug extends PolymerElement {

    static get template() {
        return html`
        <style>
            pre{
                padding: 5px;
                border: 1px solid;
            }
        </style>
        <pre>[[output]]</pre>
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

    static get observers() {
        return [
            '_dumpOut(data.*)'
        ];
    }

    _dumpOut() {
        this.output = JSON.stringify(this.data, null, 4);
    }
}

customElements.define(AppDebug.is, AppDebug);

