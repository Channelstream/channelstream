Polymer({
    is: 'chat-message-list',
    // this is required so we can pass visible/hidden state to message list and iron-list
    behaviors: [
        Polymer.IronResizableBehavior
    ],
    attached: function() {
        this.notifyResize();
    },

    properties: {
        messages: Array
    },
    observers: [
        '_messagesChanged(messages.splices)'
    ],

    _messagesChanged: function () {
        if(this.messages){
            this.$$('iron-list').scrollToIndex(this.messages.length - 1);
        }
    }
});
