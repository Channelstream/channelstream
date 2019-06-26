import {LitElement, html} from 'lit-element';
import {unsafeHTML} from 'lit-html/directives/unsafe-html.js';
import 'weightless/button/button.js';
import 'weightless/icon/icon.js';
import 'weightless/textfield/textfield.js';
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
                <wl-button fab flat inverted @click=${(e) => this.messageEdit()}>
                   <wl-icon>create</wl-icon>
                </wl-button>
                <wl-button fab flat inverted @click=${(e) => this.messageDelete()}>
                   <wl-icon>delete</wl-icon>
                </wl-button>
            `;
        }

        if (this.message.type === 'message'){
            messageText = this.message.message.text
            // insafe hack, but should be ok for simple demo
            if (messageText.includes('https://github.com/Channelstream')){
                messageText = unsafeHTML(messageText);
            }
        }
        else{
            messageText = `User ${this.message.message.action}`
        }

        if (this.edited){
            messageNode = html`
            <form onsubmit="return false;">
                <wl-textfield name="message" required label="Message"  .value="${this.message.message.text}"></wl-textfield>
                <wl-button fab flat inverted @click=${(e) => this.messageEdited(e)}>
                    <wl-icon>send</wl-icon>
                </wl-button>
            </form>`;
        }
        else{
            messageNode = html`<span class="text">${messageText}</span>`;
        }

        return html`
        <style>
            :host {
                display: block;
                --button-fab-size: 25px;
                --button-font-size: 10px;
            }

            wl-textfield{
                width: 80%;
                display: inline-block;
            }

            chat-avatar {
                float: left;
                margin-right: 15px;

                overflow: hidden;
                width: 40px;
                height: 40px;
                --chat-avatar-width: 40px;
                --chat-avatar-height: 40px;
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
        message.message.text = this.shadowRoot.querySelector('wl-textfield').value;
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
