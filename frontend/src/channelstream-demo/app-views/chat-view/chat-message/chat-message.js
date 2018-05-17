import {LitElement, html} from '@polymer/lit-element';

import '@polymer/iron-image/iron-image.js';
import '../../../chat-avatar/chat-avatar.js'


class ChatMessage extends LitElement {

    _shouldRender(props){
        if (!props.message){
            return false
        }
        return true;
    }

    _render({message}){
        return html`
        <style>
            :host {
                display: block;
            }
        
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
        <chat-avatar username=${message.user} email=${message.email}></chat-avatar>
        <div class$="message ${message.type}">
            <div>[${message.channel}] <strong>${message.user}</strong></div>
            <div><span class="timestamp">${message.timestamp.split('.')[0]}</span>:
                <span class="text">${this._messageText(message)}</span></div>
        </div>
        <br clear="both"/>
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

    _messageText(message) {
        if (message.type === 'message'){
            return message.message.text
        }
        else{
            return `User ${message.message.action}`
        }


    }
}

customElements.define(ChatMessage.is, ChatMessage);

