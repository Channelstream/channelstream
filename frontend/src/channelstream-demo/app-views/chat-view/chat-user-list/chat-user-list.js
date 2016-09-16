Polymer({
    is: 'chat-user-list',
    properties: {
        users: Array,
        usersStates: Object
    },
    _computedEmail: function (op, username) {
        return this.usersStates[username].state.email;
    }
});
