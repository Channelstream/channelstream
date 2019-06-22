const template = document.createElement('template');
template.innerHTML = `
  <style>
    *{
        box-sizing: border-box;
    }
  </style>
  <div class="collapsible">
  <slot></slot>
  </div>
`;

class UniversalCollapse extends HTMLElement {
    constructor() {
        super();
        this.transitionSpeed = '0.5s';
        this.transitioning = false;
        this.attachShadow({ mode: 'open' });
        let clonedTemplate = template.content.cloneNode(true);
        clonedTemplate.innerHTML = clonedTemplate.innerHTML;
        this.shadowRoot.appendChild(clonedTemplate);
        this.collapsibleNode = this.shadowRoot.querySelector('.collapsible');
        this.hiddenStyleText = `display: block; max-height: 0; overflow: hidden; transition: max-height ${this.transitionSpeed} cubic-bezier(0, 1, 0, 1) 0s;`;
        this.visibleStyleText = `max-height: 1600px; transition: max-height ${this.transitionSpeed} cubic-bezier(0, 1, 0, 1) 0s;`;
        this.onCollapsedChange(true);
    }

    onCollapsedChange(ignoreTransition){
        if (this.collapsed){
            this.collapsibleNode.style.cssText = this.hiddenStyleText;
        }
        else{
            this.collapsibleNode.style.cssText = this.visibleStyleText;
        }
    }

    toggle(){
        this.collapsed = !this.collapsed;
    }

    set collapsed(value) {
        this._collapsed = value;
        // boolean attrib
        if (this._collapsed) {
            this.setAttribute('collapsed', '');
        } else {
            this.removeAttribute('collapsed');
        }
        this.onCollapsedChange();
    }

    get collapsed() {
        return this._collapsed;;
    }

    static get observedAttributes() {
        return ['collapsed'];
    }

    attachedCallback(){
        this.addEventListener("transitionend", this.endTransition);
    }

    attributeChangedCallback(name, oldVal, newVal) {
        if (name === 'collapsed' && oldVal != newVal){
            this.collapsed = newVal === '';
        }
    }
}

customElements.define('universal-collapse', UniversalCollapse);
