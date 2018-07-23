import {LitElement, html} from '@polymer/lit-element';

import '@polymer/iron-image/iron-image.js';
import '@polymer/paper-icon-button/paper-icon-button.js';
import '../../../chat-avatar/chat-avatar.js'


class ChatMessage extends LitElement {

    _shouldRender(props){
        if (!props.message){
            return false
        }
        return true;
    }

    _render({message, user}){

        let editIcons = ``;
        if (message.user === user.username){
            editIcons = html`
            <paper-icon-button icon="create" on-tap=${(e) => this.messageEdit(message)}></paper-icon-button>
            <paper-icon-button icon="delete" on-tap=${(e) => this.messageDelete(message)}></paper-icon-button>
            `;
        }

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
            <div>[${message.channel}] <strong>${message.user}</strong> ${editIcons}</div>
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
            message: Object,
            user: Object
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

    messageEdit(message){
        console.log('messageEdit', {message});
        this.dispatchEvent(new CustomEvent('message-edit', {
            detail: {message},
            bubbles: true,
            composed: true
        }));
    }

    messageDelete(message){
        console.log('messageDelete', {message});
        this.dispatchEvent(new CustomEvent('message-delete', {
            detail: {message},
            bubbles: true,
            composed: true
        }));
    }

}

customElements.define(ChatMessage.is, ChatMessage);

