import {LitElement, html} from '@polymer/lit-element';

import '@polymer/iron-image/iron-image.js';
import '@polymer/paper-icon-button/paper-icon-button.js';
import '@polymer/paper-input/paper-input';
import '../../../chat-avatar/chat-avatar.js'


class ChatMessage extends LitElement {

    _shouldRender(props){
        if (!props.message){
            return false
        }
        return true;
    }

    render(){
        let editIcons = ``;
        let messageNode = ``;
        let messageText;

        if (this.message.user === this.user.username){
            editIcons = html`
            <paper-icon-button icon="create" @tap=${(e) => this.messageEdit()}></paper-icon-button>
            <paper-icon-button icon="delete" @tap=${(e) => this.messageDelete()}></paper-icon-button>
            `;
        }

        if (this.message.type === 'message'){
            messageText = this.message.message.text
        }
        else{
            messageText = `User ${this.message.message.action}`
        }

        if (this.edited){
            messageNode = html`
            <form onsubmit="return false;">
            <iron-a11y-keys id="a11y" keys="enter" @keys-pressed=${(e) => this.messageEdited(e)}></iron-a11y-keys>
                <paper-input name="message" label="Message" .value="${this.message.message.text}"></paper-input>
                <paper-icon-button icon="icons:send" @tap=${(e) => this.messageEdited(e)}></paper-icon-button>
            </form>`;
        }
        else{
            messageNode = html`<span class="text">${messageText}</span>`;
        }

        return html`
        <style>
            :host {
                display: block;
            }
        
            paper-input{
                width: 80%;
                display: inline-block;
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
        <chat-avatar .username=${this.message.user} .email=${this.message.email}></chat-avatar>
        <div class="message ${this.message.type}">
            <div>[${this.message.channel}] <strong>${this.message.user}</strong> ${editIcons}</div>
            <div><span class="timestamp">${this.message.timestamp.split('.')[0]}</span>:
                ${messageNode}</div>
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
            user: Object,
            edited: Boolean
        };
    }

    constructor(){
        super();
        // this is just for some debug fun
        this.random = Math.random();
    }

    messageEdit(){
        this.edited = true;
    }

    messageEdited(event){
        event.preventDefault();
        let message = {...this.message, message:{...this.message.message}};
        message.message.text = this.shadowRoot.querySelector('paper-input').value;
        this.edited = false;
        this.dispatchEvent(new CustomEvent('message-edit', {
            detail: message,
            bubbles: true,
            composed: true
        }));
    }

    messageDelete(){
        this.dispatchEvent(new CustomEvent('message-delete', {
            detail: {...this.message, message:{...this.message.message}},
            bubbles: true,
            composed: true
        }));
    }

}

customElements.define(ChatMessage.is, ChatMessage);

