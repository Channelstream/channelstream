import {PolymerElement, html} from '@polymer/polymer/polymer-element.js';

import '@polymer/iron-image/iron-image.js';
import '../../../chat-avatar/chat-avatar.js'


class ChatMessage extends PolymerElement {

    static get template(){
        return html`
        <style>
            chat-avatar {
                float: left;
                margin-right: 15px;

                overflow: hidden;
                width: 40px;
                height: 40px;
                --chat-avatar-mixin: {
                    width: 40px;
                    height: 40px;
                }
            }

            .message.presence, .timestamp {
                color: dimgrey;
            }

            .message .text{
                white-space: pre-line;
            }

            :host > *{
                padding: 5px;
            }

        </style>
        <chat-avatar username="[[message.message.user]]" email="[[message.message.email]]"></chat-avatar>
        <div class$="message [[message.type]]">
            <div>[[[message.channel]]] <strong>[[message.user]]</strong></div>
            <div><span class="timestamp">[[_shortTime(message.timestamp)]]</span>:
                <span class="text">[[_messageText(message.message.text)]]</span></div>
        </div>
        `
    }

    static get is() {
        return 'chat-message';
    }

    static get properties() {
        return {
            message: Object
        };
    }

    constructor(){
        super();
        // this is just for some debug fun
        this.random = Math.random();
    }

    _messageText() {
        let txt = this.message.message.action;
        return this.message.message.text || `User ${txt}`;
    }

    _shortTime() {
        return this.message.timestamp.split('.')[0];
    }
}

customElements.define(ChatMessage.is, ChatMessage);

